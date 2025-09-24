# 📖 Usage Guide

## How to Use the BTI Bot

### 1. Start the Bot
Send `/start` command to the bot in Telegram.

### 2. Enter Cadastral Number
Type a cadastral number in format: `77:09:0001013:1087`

### 3. Verify Property Data
The bot will show:
- Property address
- Area in square meters
- Construction year
- Wall materials
- Property type

Click "✅ Да, верно" to confirm or "❌ Нет, исправить" to re-enter.

### 4. Get Three Price Cards
The bot calculates:
- **Card 1 (BTI)**: Official BTI rates
- **Card 2 (Competitors)**: Market prices from competitors
- **Card 3 (Recommended)**: Optimal pricing

### 5. Generate Commercial Proposal (NEW!)
Click "📝 Коммерческое предложение" to generate a personalized business proposal using GPT.

### 6. Contact Manager
Click "📞 Связаться с менеджером" to get in touch with a manager.

## Example Conversation

```
User: /start
Bot: 🏠 Привет! Я бот для расчёта стоимости БТИ с тремя карточками цен.
     Введите кадастровый номер (например, 77:09:0001013:1087).

User: 77:09:0001013:1087
Bot: 🔍 Ищу данные по кадастру 77:09:0001013:1087 в Росреестре...

Bot: ✅ Найдены данные из Росреестра:
     📍 Адрес: г. Москва, ул. Ленина, д. 10
     📐 Площадь: 85 м²
     📅 Год постройки: 1985
     🧱 Материал стен: Кирпич
     🏢 Тип помещения: Жилое
     Данные верны?

User: [Clicks "✅ Да, верно"]
Bot: ✅ Данные приняты. Рассчитываем три карточки цен...

Bot: 📊 ТРИ КАРТОЧКИ ЦЕН для 85 м² (Жилое, Кирпич, 1985 г.):
     🏛️ КАРТОЧКА 1: БТИ (официальные тарифы)
     • Обмеры: 4,250 руб.
     • Техпаспорт + задание: 63,750 руб.
     • Итого БТИ: 68,000 руб.
     
     🏢 КАРТОЧКА 2: Конкуренты (рыночные цены)
     • Медиана конкурентов: 150 руб/м²
     • С НДС и прибылью: 101,000 руб.
     
     ⭐ КАРТОЧКА 3: Рекомендуемая цена
     • Оптимальная цена: 89,500 руб.
     
     [📄 Скачать PDF] [📝 Коммерческое предложение] [📞 Заказать услугу] [🔄 Новый расчёт]

User: [Clicks "📝 Коммерческое предложение"]
Bot: 🤖 Генерирую коммерческое предложение...

Bot: 📝 КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ
     
     Предлагаем выполнить комплексные услуги БТИ для объекта по адресу 
     г. Москва, ул. Ленина, д. 10, площадью 85 м² (жилое помещение, кирпич, 1985 г.).
     
     Наша рекомендованная стоимость составляет 89,500 руб., что включает 
     полный пакет: обмеры помещений (4,250 руб.), подготовку технического 
     паспорта и технического задания (63,750 руб.).
     
     Данная цена выгодно отличается от официальных тарифов БТИ (68,000 руб.) 
     и рыночных предложений конкурентов (101,000 руб.), обеспечивая 
     оптимальное соотношение цена-качество.
     
     Гарантируем профессиональное выполнение всех работ в установленные сроки.
     
     📞 Свяжитесь с нами для оформления заказа!
     
     [📞 Связаться с менеджером] [🔄 Новый расчёт]
```

## Features Explained

### 🤖 GPT Commercial Proposals
- **Automatic Generation**: Creates personalized business proposals
- **Professional Content**: 6-7 sentences, business tone
- **Smart Arguments**: Uses BTI and competitor data for persuasion
- **Ready to Send**: No editing required, professional quality

### 📊 Three-Price System
- **BTI Official Rates**: Government-approved pricing
- **Competitor Analysis**: Real market research via SERP API
- **Recommended Pricing**: Optimal balance between official and market rates

### 🔍 Data Sources
- **Russian State Register**: Official property data
- **SERP API**: Competitor price research
- **OpenAI GPT**: Commercial proposal generation

## Tips for Best Results

1. **Use Valid Cadastral Numbers**: Format `XX:XX:XXXXXXXX:XXXX`
2. **Verify Property Data**: Ensure accuracy before proceeding
3. **Generate Proposals**: Use GPT feature for professional client communication
4. **Contact Manager**: For complex cases or additional services

## Support

If you encounter issues:
1. Check your cadastral number format
2. Ensure stable internet connection
3. Contact support if bot doesn't respond
4. Try again with a different cadastral number
