# download_fresh.py
import subprocess
import time
from pathlib import Path
from datasets import load_dataset
import pandas as pd
from tqdm import tqdm
import random

# Конфигурация
AUDIO_DIR = Path("./musiccaps_audio_fresh")  # Новая папка!
AUDIO_DIR.mkdir(exist_ok=True)

# Путь к ffmpeg
FFMPEG_DIR = r"C:\ffmpeg\ffmpeg-8.0.1-full_build\bin"

def download_audio_segment(ytid, start_s, output_dir, max_retries=2):
    """Скачивает с проверкой результата"""
    output_path = output_dir / f"{ytid}_{int(start_s)}.wav"
    
    # Проверяем, существует ли уже нормальный файл
    if output_path.exists() and output_path.stat().st_size > 100000:  # > 100KB
        return 'exists'
    
    url = f"https://youtube.com/watch?v={ytid}"
    
    for attempt in range(max_retries):
        try:
            cmd = [
                'yt-dlp',
                '--ffmpeg-location', FFMPEG_DIR,
                '-f', 'bestaudio[ext=m4a]/bestaudio',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',
                '--postprocessor-args', '-acodec pcm_s16le -ar 44100',  # явные параметры
                '-o', str(output_path),
                '--no-playlist',
                '--quiet',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Проверяем результат
            if result.returncode == 0 and output_path.exists():
                size = output_path.stat().st_size
                if size > 100000:  # больше 100KB - нормально
                    return 'success'
                else:
                    # Слишком маленький файл - удаляем
                    output_path.unlink(missing_ok=True)
                    return 'too_small'
            
            # Проверяем ошибки
            stderr = result.stderr.lower()
            if any(msg in stderr for msg in ['video unavailable', 'private video', 'not available']):
                return 'unavailable'
                    
        except Exception as e:
            print(f"Ошибка: {e}")
        
        time.sleep(5)
    
    return 'failed'

def main():
    print("=" * 60)
    print("СВЕЖЕЕ СКАЧИВАНИЕ MUSICCAPS")
    print("=" * 60)
    
    # Загружаем метаданные
    print("\nЗагрузка метаданных...")
    dataset = load_dataset("google/MusicCaps", split="train")
    df = pd.DataFrame(dataset)
    total = len(df)
    print(f"Всего записей: {total}")
    
    # Счетчики
    stats = {'success': 0, 'exists': 0, 'unavailable': 0, 'too_small': 0, 'failed': 0}
    
    print("\nНачинаем скачивание...")
    print("(будет создана новая папка musiccaps_audio_fresh)")
    
    for idx, row in enumerate(tqdm(df.iterrows(), total=total, desc="Скачивание")):
        _, row_data = row
        ytid = row_data['ytid']
        start_s = row_data['start_s']
        
        result = download_audio_segment(ytid, start_s, AUDIO_DIR)
        stats[result] += 1
        
        if (idx + 1) % 100 == 0:
            print(f"\nПрогресс: {idx+1}/{total}")
            print(f"Успешно: {stats['success']}")
            print(f"Недоступно: {stats['unavailable']}")
            print(f"Слишком маленькие: {stats['too_small']}")
        
        time.sleep(random.uniform(1, 3))
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ:")
    print(f" Успешно: {stats['success']}")
    print(f"Уже было: {stats['exists']}")
    print(f"Недоступно: {stats['unavailable']}")
    print(f" Слишком маленькие: {stats['too_small']}")
    print(f"Ошибки: {stats['failed']}")
    print(f"Файлов в папке: {len(list(AUDIO_DIR.glob('*.wav')))}")

if __name__ == "__main__":
    response = input("\nНачать свежее скачивание? (y/n): ")
    if response.lower() == 'y':
        main()