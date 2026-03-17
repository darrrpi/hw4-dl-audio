# download_musiccaps_full.py
import pandas as pd
import subprocess
from pathlib import Path
from datasets import load_dataset
import time
from tqdm import tqdm
import random

# ===========================================
# КОНФИГУРАЦИЯ
# ===========================================
AUDIO_DIR = Path("./musiccaps_audio")
AUDIO_DIR.mkdir(exist_ok=True)

# Лог-файлы
SUCCESS_LOG = Path("./downloaded.txt")
FAILED_LOG = Path("./failed.txt")
UNAVAILABLE_LOG = Path("./unavailable.txt")

def log_to_file(filepath, ytid, start_s):
    """Записывает информацию в лог-файл"""
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f"{ytid}_{int(start_s)}\n")

def is_already_downloaded(ytid, start_s):
    """Проверяет, скачан ли файл"""
    return (AUDIO_DIR / f"{ytid}_{int(start_s)}.wav").exists()

def download_audio_segment(ytid, start_s, max_retries=2):
    """
    Скачивает 10-секундный фрагмент с YouTube
    Возвращает: 'success', 'exists', 'unavailable', 'failed'
    """
    output_path = AUDIO_DIR / f"{ytid}_{int(start_s)}.wav"
    
    if output_path.exists():
        return 'exists'
    
    url = f"https://youtube.com/watch?v={ytid}"
    
    for attempt in range(max_retries):
        try:
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio[ext=m4a]/bestaudio',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',
                '--postprocessor-args', f'-ss {start_s} -t 10',
                '-o', str(output_path),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                return 'success'
            
            if 'video unavailable' in result.stderr.lower() or 'not available' in result.stderr.lower():
                return 'unavailable'
                
        except Exception:
            pass
        
        if attempt < max_retries - 1:
            time.sleep(5)
    
    return 'failed'

def load_downloaded_set():
    """Загружает множество уже скачанных ID из лог-файла"""
    downloaded = set()
    if SUCCESS_LOG.exists():
        with open(SUCCESS_LOG, 'r') as f:
            for line in f:
                downloaded.add(line.strip())
    return downloaded

def main():
    print("=" * 60)
    print("MusicCaps Downloader")
    print("=" * 60)
    
    # Загружаем метаданные
    print("\n Загрузка метаданных.")
    dataset = load_dataset("google/MusicCaps", split="train")
    df = pd.DataFrame(dataset)
    total = len(df)
    print(f"Всего записей: {total}")
    
    # Загружаем уже скачанные
    downloaded_ids = load_downloaded_set()
    print(f"Уже скачано (по логу): {len(downloaded_ids)}")
    
    stats = {
        'success': len(downloaded_ids),
        'exists': 0,
        'unavailable': 0,
        'failed': 0,
        'skipped': 0
    }
    
    print("\nНачинаем скачивание.")
    print(f"Сохраняем в: {AUDIO_DIR}")
    print("=" * 60)
    
    for idx, row in enumerate(tqdm(df.iterrows(), total=total, desc="Прогресс")):
        _, row_data = row
        ytid = row_data['ytid']
        start_s = row_data['start_s']
        file_id = f"{ytid}_{int(start_s)}"
        
        if file_id in downloaded_ids:
            stats['skipped'] += 1
            continue
        
        if is_already_downloaded(ytid, start_s):
            stats['exists'] += 1
            log_to_file(SUCCESS_LOG, ytid, start_s)
            continue
        
        result = download_audio_segment(ytid, start_s)
        stats[result] += 1
        
        if result == 'success':
            log_to_file(SUCCESS_LOG, ytid, start_s)
        elif result == 'unavailable':
            log_to_file(UNAVAILABLE_LOG, ytid, start_s)
        elif result == 'failed':
            log_to_file(FAILED_LOG, ytid, start_s)
        
        # Короткая пауза между запросами
        time.sleep(random.uniform(1, 2))
    
    # Итоги
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ:")
    print(f"Скачано:          {stats['success']}")
    print(f"Уже было:         {stats['exists']}")
    print(f"Недоступно:       {stats['unavailable']}")
    print(f"Ошибки:           {stats['failed']}")
    print(f"Всего файлов:     {len(list(AUDIO_DIR.glob('*.wav')))}")
    print("=" * 60)

if __name__ == "__main__":
    main()