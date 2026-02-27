import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/locale_provider.dart';

class AppDictionary {
  static const Map<String, Map<String, String>> strings = {
    // --- LOGIN SCREEN ---
    'login_title': {
      'uz': 'Tizimga kirish',
      'ru': 'Вход в систему',
    },
    'hemis_login_subtitle': {
      'uz': 'HEMIS tizimidan kirish',
      'ru': 'Вход через систему HEMIS',
    },
    'login_input_label': {
      'uz': 'Login / Talaba ID',
      'ru': 'Логин / ID студента',
    },
    'login_input_error': {
      'uz': 'Iltimos loginni kiriting',
      'ru': 'Пожалуйста, введите логин',
    },
    'password_input_label': {
      'uz': 'Parol',
      'ru': 'Пароль',
    },
    'password_input_error': {
      'uz': 'Iltimos parolni kiriting',
      'ru': 'Пожалуйста, введите пароль',
    },
    'policy_agree_1': {
      'uz': 'Men ',
      'ru': 'Я ознакомился и согласен с ',
    },
    'policy_link': {
      'uz': 'Maxfiylik siyosati',
      'ru': 'Политикой конфиденциальности',
    },
    'policy_agree_2': {
      'uz': ' bilan tanishib chiqdim va qabul qilaman.',
      'ru': '.',
    },
    'login_btn': {
      'uz': 'Tizimga kirish',
      'ru': 'Войти',
    },
    'login_staff_btn': {
      'uz': 'OneID orqali kirish (xodimlar uchun)',
      'ru': 'Вход через OneID (для сотрудников)',
    },
    'login_footer_help': {
      'uz': 'Agarda login yoki parolni unutgan bo\'lsangiz, talabalar bo\'limiga murojaat qiling.',
      'ru': 'Если вы забыли логин или пароль, обратитесь в студенческий отдел.',
    },
    'login_error_banner': {
      'uz': "Parol yoki login noto'g'ri ko'rsatilgan. Qaytadan urinib ko'ring.",
      'ru': 'Неверный логин или пароль. Попробуйте еще раз.',
    },
    'policy_sheet_title': {
      'uz': 'Maxfiylik Siyosati',
      'ru': 'Политика Конфиденциальности',
    },
    'policy_accept_btn': {
      'uz': 'Tushunarli & Qabul qilaman',
      'ru': 'Понятно и Согласен',
    },

    // --- HOME SCREEN ---
    'home_greeting': {
      'uz': 'Assalomu alaykum',
      'ru': 'Здравствуйте',
    },
    'home_tab_main': {
      'uz': 'Asosiy',
      'ru': 'Главная',
    },
    'home_tab_rating': {
      'uz': 'Reyting',
      'ru': 'Рейтинг',
    },
    'home_tab_profile': {
      'uz': 'Profil',
      'ru': 'Профиль',
    },
    'balance_label': {
      'uz': 'Joriy hisobingiz',
      'ru': 'Текущий баланс',
    },
    'module_study': {
      'uz': 'O\'quv jarayoni',
      'ru': 'Учебный процесс',
    },
    'module_social': {
      'uz': 'Ijtimoiy faollik',
      'ru': 'Соц. активность',
    },
    'module_clubs': {
      'uz': 'To\'garaklar va Ishtirok',
      'ru': 'Кружки и Участие',
    },
    'module_community': {
      'uz': 'Kasaba - Jamiyat',
      'ru': 'Профсоюз - Общество',
    },
    'module_requests': {
      'uz': 'Murojatnoma',
      'ru': 'Обращения',
    },
    'module_documents': {
      'uz': 'Elektron hujjatlar',
      'ru': 'Электронные документы',
    },

    // --- PROFILE SCREEN ---
    'profile_title': {
      'uz': 'Mening Profilim',
      'ru': 'Мой профиль',
    },
    'profile_personal_info': {
      'uz': 'Shaxsiy ma\'lumotlar',
      'ru': 'Личные данные',
    },
    'profile_faculty': {
      'uz': 'Fakultet',
      'ru': 'Факультет',
    },
    'profile_direction': {
      'uz': 'Yo\'nalish',
      'ru': 'Направление',
    },
    'profile_group': {
      'uz': 'Guruh',
      'ru': 'Группа',
    },
    'profile_level': {
      'uz': 'Bosqich',
      'ru': 'Курс',
    },
    'profile_semester': {
      'uz': 'Semestr',
      'ru': 'Семестр',
    },
    'profile_logout_btn': {
      'uz': 'Tizimdan chiqish',
      'ru': 'Выйти из системы',
    },
    'profile_logout_confirm': {
      'uz': 'Haqiqatan ham chiqmoqchimisiz?',
      'ru': 'Вы действительно хотите выйти?',
    },
    'yes': {
      'uz': 'Ha',
      'ru': 'Да',
    },
    'no': {
      'uz': 'Yo\'q',
      'ru': 'Нет',
    },

    // --- SOCIAL ACTIVITY ---
    'social_title': {
      'uz': 'Ijtimoiy Faollik',
      'ru': 'Социальная активность',
    },
    'social_add_btn': {
      'uz': 'Faollik qo\'shish',
      'ru': 'Добавить активность',
    },
    'social_filter_all': {
      'uz': 'Barchasi',
      'ru': 'Все',
    },
    'social_status_approved': {
      'uz': 'Tasdiqlangan',
      'ru': 'Одобрено',
    },
    'social_status_pending': {
      'uz': 'Kutilayotgan',
      'ru': 'В ожидании',
    },
    'social_status_rejected': {
      'uz': 'Rad etilgan',
      'ru': 'Отклонено',
    },

        'btn_cancel': {
      'uz': "Bekor qilish",
      'ru': "Отмена",
    },
    'btn_submit': {
      'uz': "Yuborish",
      'ru': "Отправить",
    },
    'menu_appeals': {
      'uz': "Murojaatlar",
      'ru': "Обращения",
    },
    'msg_error_occurred': {
      'uz': "Xatolik yuz berdi",
      'ru': "Произошла ошибка",
    },
    'btn_confirm': {
      'uz': "Tasdiqlash",
      'ru': "Подтвердить",
    },
    'msg_students_not_found': {
      'uz': "Talabalar topilmadi",
      'ru': "Студенты не найдены",
    },
    'btn_edit': {
      'uz': "Tahrirlash",
      'ru': "Редактировать",
    },
    'btn_save': {
      'uz': "Saqlash",
      'ru': "Сохранить",
    },
    'btn_no': {
      'uz': "Yo'q",
      'ru': "Нет",
    },
    'btn_yes': {
      'uz': "Ha",
      'ru': "Да",
    },
    'msg_info_not_found': {
      'uz': "Ma'lumot topilmadi",
      'ru': "Информация не найдена",
    },
    'msg_invalid_amount': {
      'uz': "Summa xato kiritildi",
      'ru': "Сумма введена неверно",
    },
    'msg_library_soon': {
      'uz': "Kutubxona tez orada ishga tushadi",
      'ru': "Библиотека скоро заработает",
    },
    'msg_market_soon': {
      'uz': "Bozor bo'limi tez kunda ishga tushadi",
      'ru': "Раздел рынка скоро заработает",
    },
    'btn_vote': {
      'uz': "Ovoz berish",
      'ru': "Голосовать",
    },
    'msg_premium_required': {
      'uz': "Premium kerak",
      'ru': "Требуется Premium",
    },
    'tab_students': {
      'uz': "Talabalar",
      'ru': "Студенты",
    },
    'msg_groups_not_found': {
      'uz': "Guruhlar topilmadi",
      'ru': "Группы не найдены",
    },
    'menu_settings': {
      'uz': "Sozlamalar",
      'ru': "Настройки",
    },
    'menu_documents': {
      'uz': "Hujjatlar",
      'ru': "Документы",
    },
    'menu_help': {
      'uz': "Yordam",
      'ru': "Помощь",
    },
    'btn_new_chat': {
      'uz': "Yangi Suhbat",
      'ru': "Новый чат",
    },
    'btn_regenerate': {
      'uz': "Qayta shakllantirish",
      'ru': "Перегенерировать",
    },
    'msg_no_data': {
      'uz': "Ma'lumot yo'q",
      'ru': "Нет данных",
    },
    'msg_write_or_select_file': {
      'uz': "Iltimos, matn yozing yoki fayl tanlang.",
      'ru': "Пожалуйста, введите текст или выберите файл.",
    },
    'btn_select_file': {
      'uz': "Fayl tanlash",
      'ru': "Выбрать файл",
    },
    'btn_copy': {
      'uz': "Nusxa olish",
      'ru': "Копировать",
    },
    'btn_new_activity': {
      'uz': "Yangi Faollik",
      'ru': "Новая активность",
    },
    'msg_clubs_load_error': {
      'uz': "Klublarni yuklashda xatolik yuz berdi",
      'ru': "Ошибка загрузки клубов",
    },
    'msg_changes_saved': {
      'uz': "O'zgarishlar saqlandi",
      'ru': "Изменения сохранены",
    },
    'msg_joined_club': {
      'uz': "A'zo bo'ldingiz",
      'ru': "Вы вступили",
    },
    'msg_no_members_yet': {
      'uz': "Hozircha a'zolar yo'q",
      'ru': "Пока нет участников",
    },
    'btn_kick': {
      'uz': "Chiqarish",
      'ru': "Исключить",
    },
    'msg_student_kicked': {
      'uz': "Talaba chiqarib yuborildi",
      'ru': "Студент исключен",
    },
    'btn_send_to_telegram': {
      'uz': "Telegram kanalga ham yuborish",
      'ru': "Отправить также в Telegram канал",
    },
    'msg_nothing_here': {
      'uz': "Hech narsa yo'q",
      'ru': "Здесь ничего нет",
    },
    'msg_no_events_yet': {
      'uz': "Hozircha tadbirlar yo'q",
      'ru': "Пока нет мероприятий",
    },
    'btn_add_or_edit': {
      'uz': "Qo'shimcha yoki Tahrirlash",
      'ru': "Дополнительно или Редактировать",
    },
    'msg_list_empty': {
      'uz': "Hozircha ra'yxat bo'sh",
      'ru': "Пока список пуст",
    },
    'msg_action_failed_check_data': {
      'uz': "Bajarilmadi. Barcha ma'lumotlar to'g'riligini tekshiring.",
      'ru': "Не выполнено. Проверьте правильность всех данных.",
    },
    'btn_read_ebook': {
      'uz': "Elektron o'qish",
      'ru': "Читать электронно",
    },
    'msg_cancelled': {
      'uz': "Bekor qilindi",
      'ru': "Отменено",
    },
    'msg_book_not_found': {
      'uz': "Kitob topilmadi",
      'ru': "Книга не найдена",
    },
    'msg_book_info_not_found': {
      'uz': "Kitob ma'lumotlari topilmadi",
      'ru': "Информация об книге не найдена",
    },
    'btn_details': {
      'uz': "Batafsil",
      'ru': "Подробнее",
    },
    'lib_available_only': {
      'uz': "Faqat mavjud kitoblar",
      'ru': "Только имеющиеся книги",
    },
    'lib_has_ebook': {
      'uz': "Elektron variant bor",
      'ru': "Есть электронный вариант",
    },

    // Default Fallbacks
    'error': {
      'uz': 'Xatolik',
      'ru': 'Ошибка',
    },
    'success': {
      'uz': 'Muvaffaqiyatli',
      'ru': 'Успешно',
    },
  };

  static String tr(BuildContext context, String key) {
    // We intentionally do NOT listen here if we plan to use it strictly in build methods
    // that already depend on LocaleProvider OR we can subscribe depending on usage.
    // The safest way is to watch LocaleProvider inside the widgets and pass to `tr`.
    final localeProvider = Provider.of<LocaleProvider>(context);
    final langCode = localeProvider.locale.languageCode;
    
    final node = strings[key];
    if (node == null) return key; // Fallback to key if not found
    
    return node[langCode] ?? node['uz'] ?? key;
  }
}
