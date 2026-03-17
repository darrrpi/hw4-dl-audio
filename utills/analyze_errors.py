# retry_failed_fixed.py
import subprocess
import time
from pathlib import Path
from tqdm import tqdm
import random

# Конфигурация
AUDIO_DIR = Path("./musiccaps_audio")
SUCCESS_LOG = Path("./downloaded.txt")
FAILED_LOG = Path("./failed.txt")
UNAVAILABLE_LOG = Path("./unavailable.txt")

def load_sets():
    """Загружает все множества ID"""
    downloaded = set()
    if SUCCESS_LOG.exists():
        with open(SUCCESS_LOG, 'r') as f:
            downloaded.update(line.strip() for line in f)
    
    failed = set()
    if FAILED_LOG.exists():
        with open(FAILED_LOG, 'r') as f:
            failed.update(line.strip() for line in f)
    
    unavailable = set()
    if UNAVAILABLE_LOG.exists():
        with open(UNAVAILABLE_LOG, 'r') as f:
            unavailable.update(line.strip() for line in f)
    
    return downloaded, failed, unavailable

def parse_file_id(file_id):
    """Безопасно парсит file_id в ytid и start_s"""
    # Разделяем по последнему подчеркиванию
    parts = file_id.rsplit('_', 1)
    if len(parts) != 2:
        print(f"⚠️ Странный формат ID: {file_id}")
        return None, None
    
    ytid, start_s = parts
    try:
        start_s = int(start_s)
        return ytid, start_s
    except ValueError:
        print(f"⚠️ Не удалось преобразовать start_s: {start_s}")
        return None, None

def download_with_retry(ytid, start_s):
    """Расширенная версия с большим количеством попыток"""
    output_path = AUDIO_DIR / f"{ytid}_{int(start_s)}.wav"
    
    if output_path.exists():
        return 'success'
    
    url = f"https://youtube.com/watch?v={ytid}"
    
    # Расширенный список форматов и параметров
    strategies = [
        # Стратегия 1: m4a с обычным user-agent
        {
            'format': 'bestaudio[ext=m4a]',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
            'extra': []
        },
        # Стратегия 2: webm с Firefox user-agent
        {
            'format': 'bestaudio[ext=webm]',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'extra': []
        },
        # Стратегия 3: любой формат с Safari
        {
            'format': 'bestaudio',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15',
            'extra': ['--youtube-skip-dash-manifest']
        },
        # Стратегия 4: без проверки сертификатов
        {
            'format': 'bestaudio',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'extra': ['--no-check-certificate']
        },
        # Стратегия 5: мобильный user-agent
        {
            'format': 'bestaudio',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148',
            'extra': []
        },
        # Стратегия 6: с куками (если есть)
        {
            'format': 'bestaudio',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'extra': ['--cookies', 'cookies.txt'] if Path('cookies.txt').exists() else []
        },
    ]
    
    for strategy_num, strategy in enumerate(strategies, 1):
        try:
            cmd = [
                'yt-dlp',
                '-f', strategy['format'],
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',
                '--postprocessor-args', f'-ss {start_s} -t 10',
                '-o', str(output_path),
                '--no-playlist',
                '--quiet',
                '--no-warnings',
                '--user-agent', strategy['user_agent'],
                '--extractor-retries', '5',
                '--fragment-retries', '5',
            ]
            
            # Добавляем дополнительные параметры
            if strategy['extra']:
                cmd.extend(strategy['extra'])
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                print(f"✅ Успешно со стратегией {strategy_num}")
                return 'success'
            
            # Анализ ошибки
            stderr = result.stderr.lower()
            if any(msg in stderr for msg in [
                'video unavailable', 
                'private video', 
                'this video is not available',
                'removed by user',
                'uploader has closed'
            ]):
                return 'unavailable'
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Таймаут стратегии {strategy_num}")
        except Exception as e:
            print(f"⚠️ Ошибка стратегии {strategy_num}: {str(e)[:50]}")
            continue
    
    return 'failed'

def main():
    print("=" * 60)
    print("🔄 ПЕРЕКАЧИВАНИЕ ПРОБЛЕМНЫХ ФАЙЛОВ (ИСПРАВЛЕННАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    # Загружаем все ID
    downloaded, failed, unavailable = load_sets()
    
    print(f"\n📊 Текущая статистика:")
    print(f"✅ Уже скачано: {len(downloaded)}")
    print(f"❌ В failed.log: {len(failed)}")
    print(f"🔒 В unavailable.log: {len(unavailable)}")
    
    # Находим файлы для перекачивания
    to_retry = []
    invalid_ids = []
    
    for file_id in (failed - unavailable - downloaded):
        ytid, start_s = parse_file_id(file_id)
        if ytid and start_s is not None:
            to_retry.append((file_id, ytid, start_s))
        else:
            invalid_ids.append(file_id)
    
    print(f"\n🔄 Будем пробовать перекачать: {len(to_retry)} файлов")
    if invalid_ids:
        print(f"⚠️ Пропущено некорректных ID: {len(invalid_ids)}")
        print(f"   Пример: {invalid_ids[:3]}")
    
    if not to_retry:
        print("✅ Нет файлов для перекачивания")
        return
    
    print("\n🔍 Первые 10 для перекачивания:")
    for i, (file_id, ytid, start_s) in enumerate(to_retry[:10]):
        print(f"  {i+1}. {ytid} (start: {start_s}s)")
    
    response = input(f"\n🚀 Начать перекачивание {len(to_retry)} файлов? (y/n): ")
    if response.lower() != 'y':
        return
    
    # Статистика
    stats = {'success': 0, 'failed': 0, 'unavailable': 0}
    
    # Перекачиваем
    for i, (file_id, ytid, start_s) in enumerate(tqdm(to_retry, desc="Перекачивание")):
        print(f"\n[{i+1}/{len(to_retry)}] {ytid}...")
        
        result = download_with_retry(ytid, start_s)
        stats[result] += 1
        
        if result == 'success':
            print(f"✅ УСПЕХ! Файл скачан")
            with open(SUCCESS_LOG, 'a') as f:
                f.write(f"{file_id}\n")
                
        elif result == 'unavailable':
            print(f"🔒 Видео недоступно")
            with open(UNAVAILABLE_LOG, 'a') as f:
                f.write(f"{file_id}\n")
        else:
            print(f"❌ Снова ошибка")
        
        # Пауза между запросами
        time.sleep(random.uniform(3, 5))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ПЕРЕКАЧИВАНИЯ:")
    print(f"✅ Дополнительно скачано: {stats['success']}")
    print(f"🔒 Подтверждено недоступно: {stats['unavailable']}")
    print(f"❌ Осталось ошибок: {stats['failed']}")
    
    # Показываем обновленную статистику
    new_total = len(list(AUDIO_DIR.glob('*.wav')))
    print(f"📁 Всего файлов теперь: {new_total}")
    print("=" * 60)

if __name__ == "__main__":
    main()