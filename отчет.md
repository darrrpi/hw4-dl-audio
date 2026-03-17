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

## Запуск обучения ##

Это был технически самый тяжелый этап для меня. Подробнее расскажу на этапе сложностей, с которыми столкнулась.

### Конфигурация Hydra ###
Файл: configs/dset/audio/musiccaps_ft.yaml
   
    datasource:
      max_sample_rate: 44100
      max_channels: 2
      train: egs/musiccaps/train
      valid: egs/musiccaps/valid
      evaluate: egs/musiccaps/valid
      generate: egs/musiccaps/valid

      # @package _global_
      
Файл: configs/experiment/musiccaps_train.yaml

      
    defaults:
      - /lm: musicgen_lm
      - /conditioner: text2music
      - _self_
    
    # Датасет
    dset: audio/musiccaps_ft
    
    dataset:
      batch_size: 1
      num_workers: 0
      segment_duration: 10
      return_info: true
      train:
        num_samples: 3064
      valid:
        num_samples: 306
    
    # Оптимизатор
    optimizer:
      lr: 8e-6
      betas: [0.9, 0.999]
      weight_decay: 0.01
    
    # Параметры обучения
    training_epochs: 16
    updates_per_epoch: 3064
    evaluate:
      every: 4
    generate:
      every: 4
    
    # Устройство
    device: cpu
    fp16: false
    
    # Conditioner
    conditioner:
      text:
        merge_text_p: 0.25
        drop_desc_p: 0.5
        drop_other_p: 0.5
        text_attributes: [genre_tags, general_mood, lead_instrument, 
                          accompaniment, tempo_and_rhythm, vocal_presence, 
                          production_quality]

      

    
## Запуск обучения ##

    AUDIOCRAFT_DORA_DIR=$(pwd)/../outputs \
    dora --package audiocraft --main_module train run --clear \
      solver=musicgen/musicgen_base_32khz \
      dset=audio/musiccaps_ft \
      conditioner=text2music \
      datasource.train=$(pwd)/../egs/musiccaps/train/data.jsonl.gz \
      datasource.valid=$(pwd)/../egs/musiccaps/valid/data.jsonl.gz \
      datasource.evaluate=$(pwd)/../egs/musiccaps/valid/data.jsonl.gz \
      datasource.generate=$(pwd)/../egs/musiccaps/valid/data.jsonl.gz \
      datasource.max_sample_rate=44100 \
      datasource.max_channels=2 \
      +dataset.info_fields_required=false \
      dataset.segment_duration=10 \
      dataset.batch_size=1 \
      dataset.num_workers=0 \
      dataset.train.num_samples=3064 \
      dataset.valid.num_samples=306 \
      optim.updates_per_epoch=3064 \
      optim.epochs=16 \
      evaluate.every=4 \
      generate.every=4 \
      device=cpu \
      autocast=false \
      transformer_lm.memory_efficient=false \
      +conditioners.description.t5.autocast_dtype=null \
      optim.ema.device=cpu

## Генерация музыки ##

Скрипт загружает обученную модель и генерирует 5 треков по заданным промптам.

    python src/generate.py \
      --checkpoint outputs/xps/7a2d19bc/checkpoint.th \
      --output-dir generated \
      --duration 10

## Трудности в процессе выполнения ###

1. Во-первых, вес .waw файлов достаточно высокий, поэтому, когда появилась необходимость перенести уже обработанные данные перед обучение на другое устройство, размер датасета составил около 200 гб. Но переведя данные в формат .mp3 удалось решить данную проблему.
2. Самым сложным оказался процесс обучения данной модели, так как сборка AudioCraft достаточно избирательна и требовала тонкой настройки. Ввиду этого собрать библиотеки, требуемые для обучения на GPU оказалось достаточно сложной проблемой, поэтому было решено перенести все данные на macOS. Когда все библиотеки наконец были собраны и не конфликтовали друг с другом, возникли сложности с обучением на MPS. К сожалению, поэтому пришлось провести обучение на CPU. Это, в свою очередь, послужило причиной для медленного обучения модели, поэтому к моменту отправки ДЗ результаты обучения и генерации неутешительны.

Выводы:
1. Проверять вес данных и в случае необходимости своевременно найти альтернативу формату данных.
2. Тонкая настройка конфигурации и требуемых библиотек при обучении модели - очень важный момент, к которому стоит относиться с большей ответственностью.
