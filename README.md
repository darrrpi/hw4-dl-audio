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

### Скрипт загружает 10-секундные аудиофрагменты из YouTube по ссылкам из датасета MusicCaps, не скачивая видео целиком.



    
