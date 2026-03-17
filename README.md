# **Fine-tuning MusicGen на MusicCaps**

Данный проект выполняет **fine-tuning** модели **MusicGen-small** на датасете MusicCaps 
с использованием структурированных метаданных, обогащенных через LLM. Выполнен в рамках **4 ДЗ по курсу DLA**.

## Установка и настройка:
### 1. Клонирование репозитория
    ```
    git clone https://github.com/yourusername/hw4-dl-audio.git
    cd hw4-dl-audio
    ```
    

### 2. Установка системных зависимостей (на macOS)
    ```
    # Установка Homebrew 
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Установка FFmpeg (версия 4 для совместимости с av)
    brew install ffmpeg@4
    brew link --overwrite ffmpeg@4
    
    # Установка yt-dlp
    brew install yt-dlp
    
    # Установка micromamba (рекомендуется)
    brew install micromamba
    ```
    ```
    # Обновление pip
    pip install --upgrade pip setuptools wheel
    
    # Установка PyTorch (точные версии)
    pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0
    
    # Установка остальных зависимостей
    pip install -r requirements.txt
    ```
    
    ```
    cd audiocraft
    pip install -e . --no-deps
    cd ..
    ```


## Сбор данных MusicCaps

Скрипт загружает 10-секундные аудиофрагменты из YouTube по ссылкам из датасета MusicCaps, не скачивая видео целиком.

### Запуск
     ```
     python src/utills/download_musiccaps.py --output-dir data/musiccaps_audio --limit 4000
     ```
### Результаты
Всего записей: **5521**
Было загружено: **3922**
Недоступно видео: **942**
Ошибки скачивания: **657**

На данном этапе была сложность с скачиванием, ввиду наличия недоступных записей, тем самым набор данных сокращается. 
Также на территории РФ необходимо воспользоваться VPN, так как иначе нет доступа к сервису YouTube.

## Обогащение метаданных через LLM

В качестве LLM для данного задания было выбрано локальеное использование Llama 3 через Ollama. 

### Настройки Llama 3: ###
    ```
    # Установка Ollama
    curl -fsSL https://ollama.com/install.sh | sh

    # Запуск сервера
    ollama serve
    
    # В другом окне - загрузка модели
    ollama pull llama3.2:3b
    ```
### Запуск ###
    
    python src/enrich_metadata.py --input-dir data/musiccaps_audio --output-dir data/musiccaps_json --limit 3064

### Пример обогащения: ###

    До:
    "The low quality recording features a ballad song that contains sustained strings, mellow piano melody, soft and mellow     female vocals and subtle percussion."

    После:
    {
      "description": "The low quality recording features a ballad song that contains sustained strings, mellow piano melody, soft and mellow female vocals and subtle percussion.",
      "general_mood": "sad, mellow",
      "genre_tags": ["ballad", "pop"],
      "lead_instrument": "female vocals",
      "accompaniment": "strings, piano, percussion",
      "tempo_and_rhythm": "slow",
      "vocal_presence": "soft female vocals",
      "production_quality": "low quality"
    }

### Модификация AudioCraft ###   

Были внесены изменения в файл audiocraft/data/music_dataset.py для поддержки новых полей из JSON.

## Подготовка манифестов ##

Скрипт создает манифесты в формате .jsonl.gz для обучения и валидации.

### Запуск
    python src/utills/create_manifests.py \
      --audio-dir data/musiccaps_audio \
      --json-dir data/musiccaps_json \
      --output-dir data/manifests \
      --train-split 0.9

      


    
