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
      'uz': 'Salom',
      'ru': 'Привет',
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
      'uz': 'Akademik bo\'lim',
      'ru': 'Академический отдел',
    },
    'module_social': {
      'uz': 'Ijtimoiy Faollik',
      'ru': 'Социальная активность',
    },
    'module_clubs': {
      'uz': 'Klublar',
      'ru': 'Клубы',
    },
    'module_community': {
      'uz': 'Kutubxona',
      'ru': 'Библиотека',
    },
    'module_requests': {
      'uz': 'Murojaatlar',
      'ru': 'Обращения',
    },
    'module_documents': {
      'uz': 'Hujjatlar',
      'ru': 'Документы',
    },
    'module_certificates': {
      'uz': 'Sertifikatlar',
      'ru': 'Сертификаты',
    },
    'lbl_services': {
      'uz': 'Xizmatlar',
      'ru': 'Услуги',
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

        'msg_error': {
      'uz': "Xatolik",
      'ru': "Ошибка",
    },
    'btn_reply': {
      'uz': "Javob berish",
      'ru': "Ответить",
    },
    'msg_appeal_closed_2': {
      'uz': "Murojaat yopildi",
      'ru': "Обращение закрыто",
    },
    'lbl_appeal_answer': {
      'uz': "Murojaatga javob",
      'ru': "Ответ на обращение",
    },
    'btn_send_via_bot': {
      'uz': "Bot orqali yuborish",
      'ru': "Отправить через бот",
    },
    'msg_error_occurred_2': {
      'uz': "Xatolik yuz berdi.",
      'ru': "Произошла ошибка.",
    },
    'lbl_telegram': {
      'uz': "Telegram",
      'ru': "Telegram",
    },
    'msg_please_enter_cert_name': {
      'uz': "Iltimos, sertifikat nomini kiriting",
      'ru': "Пожалуйста, введите название сертификата",
    },
    'lbl_tutor_cabinet': {
      'uz': "Tyutor Kabineti",
      'ru': "Кабинет тьютора",
    },
    'btn_reject': {
      'uz': "Rad etish",
      'ru': "Отклонить",
    },
    'lbl_my_groups': {
      'uz': "Guruhlarim",
      'ru': "Мои группы",
    },
    'msg_chat_deleted': {
      'uz': "Chat muvaffaqiyatli o'chirildi",
      'ru': "Чат успешно удален",
    },
    'lbl_all_faculties': {
      'uz': "Barcha fakultetlar",
      'ru': "Все факультеты",
    },
    'lbl_all_universities': {
      'uz': "Barcha universitetlar",
      'ru': "Все университеты",
    },
    'lbl_my_faculty': {
      'uz': "Mening fakultetim",
      'ru': "Мой факультет",
    },
    'lbl_my_university': {
      'uz': "Mening universitetim",
      'ru': "Мой университет",
    },
    'msg_user_not_found': {
      'uz': "Foydalanuvchi topilmadi",
      'ru': "Пользователь не найден",
    },
    'lbl_edit_message': {
      'uz': "Xabarni tahrirlash",
      'ru': "Редактировать сообщение",
    },
    'msg_please_write_text': {
      'uz': "Iltimos, matn yozing!",
      'ru': "Пожалуйста, напишите текст!",
    },
    'msg_no_one_found': {
      'uz': "Hech kim topilmadi",
      'ru': "Никто не найден",
    },
    'lbl_edit_comment': {
      'uz': "Sharhni tahrirlash",
      'ru': "Редактировать комментарий",
    },
    'msg_please_write_appeal': {
      'uz': "Iltimos, murojaat matnini yozing",
      'ru': "Пожалуйста, напишите текст обращения",
    },
    'lbl_loading': {
      'uz': "Yuklanmoqda...",
      'ru': "Загрузка...",
    },
    'btn_retry': {
      'uz': "Qayta urinish",
      'ru': "Повторить",
    },
    'msg_passwords_mismatch': {
      'uz': "Parollar mos kelmadi",
      'ru': "Пароли не совпадают",
    },
    'msg_topics_not_found': {
      'uz': "Mavzular topilmadi",
      'ru': "Темы не найдены",
    },
    'msg_subject_id_not_found': {
      'uz': "Fan ID topilmadi",
      'ru': "ID предмета не найден",
    },
    'msg_confirm_vote': {
      'uz': "Ovoz berishni tasdiqlaysizmi?",
      'ru': "Подтверждаете голосование?",
    },
    'msg_vote_accepted': {
      'uz': "Ovozingiz muvaffaqiyatli qabul qilindi!",
      'ru': "Ваш голос успешно принят!",
    },
    'lbl_app_intro': {
      'uz': "Dastur bilan tanishish",
      'ru': "Ознакомление с программой",
    },
    'msg_enter_doc_name': {
      'uz': "Iltimos, hujjat nomini kiriting",
      'ru': "Пожалуйста, введите название документа",
    },
    'msg_premium_unavailable': {
      'uz': "Premium imkoniyatlari hozirda mavjud emas.",
      'ru': "Премиум-возможности сейчас недоступны.",
    },
    'btn_yes_start': {
      'uz': "Ha, boshlash",
      'ru': "Да, начать",
    },
    'lbl_account_status': {
      'uz': "Hisob holati",
      'ru': "Статус аккаунта",
    },
    'btn_select_gallery': {
      'uz': "Galereyadan tanlash",
      'ru': "Выбрать из галереи",
    },
    'lbl_social_activities': {
      'uz': "Ijtimoiy Faolliklar",
      'ru': "Социальные активности",
    },
    'lbl_profile': {
      'uz': "Profil",
      'ru': "Профиль",
    },
    'msg_fill_all_fields': {
      'uz': "Barcha maydonlarni to'ldiring",
      'ru': "Заполните все поля",
    },
    'msg_please_upload_image_first': {
      'uz': "Iltimos, avval rasm yuklang!",
      'ru': "Пожалуйста, сначала загрузите фото!",
    },
    'lbl_notifications': {
      'uz': "Xabarnomalar",
      'ru': "Уведомления",
    },

        'hint_writing_answer': {
      'uz': "Javob yozish...",
      'ru': "Написание ответа...",
    },
    'hint_enter_answer_text': {
      'uz': "Javob matnini kiriting...",
      'ru': "Введите текст ответа...",
    },
    'msg_answer_sent_success': {
      'uz': "Javob muvaffaqiyatli yuborildi",
      'ru': "Ответ успешно отправлен",
    },
    'msg_hemis_copied': {
      'uz': "HEMIS ID nusxalandi",
      'ru': "HEMIS ID скопирован",
    },
    'btn_copy_hemis_id': {
      'uz': "HEMIS ID nusxalash",
      'ru': "Скопировать HEMIS ID",
    },
    'hint_name_or_hemis': {
      'uz': "Ism yoki Hemis ID...",
      'ru': "Имя или Hemis ID...",
    },
    'msg_sending_to_tg': {
      'uz': "Telegramga yuborilmoqda...",
      'ru': "Отправка в Telegram...",
    },
    'msg_preparing_zip': {
      'uz': "ZIP arxiv tayyorlanmoqda...",
      'ru': "Подготовка ZIP-архива...",
    },
    'hint_market_search': {
      'uz': "Kitob, texnika yoki ish qidiring...",
      'ru': "Ищите книги, технику или работу...",
    },
    'msg_sending_cert_to_bot': {
      'uz': "Sertifikat botga yuborilmoqda...",
      'ru': "Отправка сертификата в бот...",
    },
    'msg_old_account_disconnected_new': {
      'uz': "Eski hisob uzildi. Yangi hisob ulang.",
      'ru': "Старый аккаунт отключен. Подключите новый.",
    },
    'hint_example_cert': {
      'uz': "Masalan: IELTS, IT-Park va h.k.",
      'ru': "Например: IELTS, IT-Park и т.д.",
    },
    'msg_cert_saved_success': {
      'uz': "Sertifikat muvaffaqiyatli saqlandi!",
      'ru': "Сертификат успешно сохранен!",
    },
    'lbl_cert_name': {
      'uz': "Sertifikat nomi",
      'ru': "Название сертификата",
    },
    'hint_search_group': {
      'uz': "Guruhni qidiring...",
      'ru': "Поиск группы...",
    },
    'msg_sending_to_tg_bot': {
      'uz': "Telegram botga yuborilmoqda...",
      'ru': "Отправка в Telegram бот...",
    },
    'msg_coming_soon': {
      'uz': "Tez kunda ishga tushadi",
      'ru': "Скоро запустится",
    },
    'lbl_activity_stats': {
      'uz': "Faolliklar Statistikasi",
      'ru': "Статистика активностей",
    },
    'lbl_docs_stats': {
      'uz': "Hujjatlar Statistikasi",
      'ru': "Статистика документов",
    },
    'hint_search_student_name': {
      'uz': "Talaba ismini qidiring...",
      'ru': "Поиск имени студента...",
    },
    'hint_write_answer': {
      'uz': "Javob yozing...",
      'ru': "Напишите ответ...",
    },
    'lbl_attendance': {
      'uz': "Davomat",
      'ru': "Посещаемость",
    },
    'lbl_activities': {
      'uz': "Faolliklar",
      'ru': "Активности",
    },
    'lbl_clubs_2': {
      'uz': "Klublar",
      'ru': "Клубы",
    },
    'lbl_library_2': {
      'uz': "Kutubxona",
      'ru': "Библиотека",
    },
    'lbl_appeals_2': {
      'uz': "Murojaatlar",
      'ru': "Обращения",
    },
    'lbl_certs_2': {
      'uz': "Sertifikatlar",
      'ru': "Сертификаты",
    },
    'lbl_my_students': {
      'uz': "Talabalarim",
      'ru': "Мои студенты",
    },
    'hint_write_answer_here': {
      'uz': "Javobingizni shu yerga yozing...",
      'ru': "Пишите ваш ответ здесь...",
    },
    'msg_answer_sent_tick': {
      'uz': "✅ Javob yuborildi",
      'ru': "✅ Ответ отправлен",
    },
    'hint_write_opinion': {
      'uz': "Fikringizni yozing...",
      'ru': "Напишите ваше мнение...",
    },
    'msg_username_saved': {
      'uz': "Username saqlandi!",
      'ru': "Юзернейм сохранен!",
    },
    'msg_msg_send_error': {
      'uz': "Xabar yuborishda xatolik",
      'ru': "Ошибка отправки сообщения",
    },
    'hint_new_text': {
      'uz': "Yangi matn...",
      'ru': "Новый текст...",
    },
    'hint_type_here': {
      'uz': "Bu yerga yozing...",
      'ru': "Пишите здесь...",
    },
    'hint_select_faculty_opt': {
      'uz': "Fakultetni tanlang (Ixtiyoriy)",
      'ru': "Выберите факультет (Необязательно)",
    },
    'hint_title_opt': {
      'uz': "Sarlavha (Ixtiyoriy)",
      'ru': "Заголовок (Необязательно)",
    },
    'lbl_faculty_dean': {
      'uz': "🎓  Fakultet (Dekanat)",
      'ru': "🎓  Факультет (Деканат)",
    },
    'lbl_university_all': {
      'uz': "🏛️  Universitet (Barchaga)",
      'ru': "🏛️  Университет (Всем)",
    },
    'hint_share_options': {
      'uz': "Telegram, Instagram, SMS va boshqalar",
      'ru': "Telegram, Instagram, SMS и другие",
    },
    'msg_saving_post': {
      'uz': "Post saqlanmoqda... ⏳",
      'ru': "Сохранение поста... ⏳",
    },
    'msg_upload_file_to_bot': {
      'uz': "Botga fayl yuklang",
      'ru': "Загрузите файл в бот",
    },
    'msg_old_account_disconnected_retry': {
      'uz': "Eski hisob uzildi. Qayta yuborishni bosing.",
      'ru': "Старый аккаунт отключен. Нажмите «Отправить повторно».",
    },
    'msg_answer_send_error': {
      'uz': "Javob yuborishda xatolik yuz berdi",
      'ru': "Ошибка при отправке ответа",
    },
    'btn_select_category': {
      'uz': "Kategoriyani tanlang",
      'ru': "Выберите категорию",
    },
    'msg_appeal_sent_success': {
      'uz': "Murojaat muvaffaqiyatli yuborildi!",
      'ru': "Обращение успешно отправлено!",
    },
    'msg_appeal_not_found': {
      'uz': "Murojaat topilmadi",
      'ru': "Обращение не найдено",
    },
    'hint_appeal_details': {
      'uz': "Murojaatingizni batafsil yozing...",
      'ru': "Напишите подробнее ваше обращение...",
    },
    'hint_select_status': {
      'uz': "Statusni tanlang",
      'ru': "Выберите статус",
    },
    'msg_bot_opened_upload_file': {
      'uz': "Telegram bot ochildi. Iltimos, u yerda faylni (Rasm/PDF) yuklang.",
      'ru': "Telegram бот открыт. Пожалуйста, загрузите туда файл (Фото/PDF).",
    },
    'msg_unanswered_questions': {
      'uz': "Barcha savollarga javob berilmadi. Davom ettirmoqchimisiz?",
      'ru': "Не на все вопросы даны ответы. Продолжить?",
    },
    'lbl_attention': {
      'uz': "Diqqat",
      'ru': "Внимание",
    },
    'hint_enter_your_answer': {
      'uz': "Javobingizni kiriting...",
      'ru': "Введите ваш ответ...",
    },
    'lbl_email': {
      'uz': "Email",
      'ru': "Email",
    },
    'hint_reenter_password': {
      'uz': "Parolni qayta kiriting",
      'ru': "Введите пароль еще раз",
    },
    'hint_confirm_password': {
      'uz': "Parolni tasdiqlash",
      'ru': "Подтверждение пароля",
    },
    'lbl_phone_number': {
      'uz': "Telefon raqam",
      'ru': "Номер телефона",
    },
    'hint_new_password': {
      'uz': "Yangi parol",
      'ru': "Новый пароль",
    },
    'msg_sending_to_bot': {
      'uz': "Botga yuborilmoqda... ⏳",
      'ru': "Отправка в бот... ⏳",
    },
    'msg_file_sent_to_tg': {
      'uz': "Fayl Telegram botingizga yuborildi ✅",
      'ru': "Файл отправлен в ваш Telegram бот ✅",
    },
    'msg_bot_start_error': {
      'uz': "Xatolik: Bot ishga tushganligini tekshiring ❌",
      'ru': "Ошибка: Проверьте, запущен ли бот ❌",
    },
    'msg_sending_doc_to_bot': {
      'uz': "Hujjat botga yuborilmoqda...",
      'ru': "Отправка документа в бот...",
    },
    'msg_doc_saved_success': {
      'uz': "Hujjat muvaffaqiyatli saqlandi!",
      'ru': "Документ успешно сохранен!",
    },
    'lbl_doc_name': {
      'uz': "Hujjat nomi",
      'ru': "Название документа",
    },
    'msg_one_time_use_continue': {
      'uz': "Ushbu imkoniyatdan faqat bir marta foydalana olasiz. Davom etasizmi?",
      'ru': "Вы можете использовать эту возможность только один раз. Продолжить?",
    },
    'lbl_username': {
      'uz': "Foydalanuvchi nomi",
      'ru': "Имя пользователя",
    },
    'lbl_hemis_login': {
      'uz': "HEMIS Login",
      'ru': "Логин HEMIS",
    },
    'lbl_hemis_password': {
      'uz': "HEMIS Parol",
      'ru': "Пароль HEMIS",
    },
    'msg_preparing_image': {
      'uz': "Rasm tayyorlanmoqda...",
      'ru': "Подготовка изображения...",
    },
    'msg_uploading_image': {
      'uz': "Rasm yuklanmoqda...",
      'ru': "Загрузка фото...",
    },
    'msg_image_upload_error': {
      'uz': "Rasm yuklashda xatolik!",
      'ru': "Ошибка загрузки фото!",
    },
    'msg_image_process_error': {
      'uz': "Rasmni qayta ishlashda xatolik",
      'ru': "Ошибка обработки фото",
    },
    'msg_stages_not_found': {
      'uz': "Bosqichlar topilmadi",
      'ru': "Этапы не найдены",
    },
    'msg_activity_rejected': {
      'uz': "Faollik rad etildi",
      'ru': "Активность отклонена",
    },
    'msg_activity_approved': {
      'uz': "Faollik tasdiqlandi",
      'ru': "Активность подтверждена",
    },
    'hint_enter_reason_opt': {
      'uz': "Sababini kiriting (ixtiyoriy)",
      'ru': "Введите причину (по желанию)",
    },
    'lbl_pending_activities': {
      'uz': "Kutilayotgan Faolliklar",
      'ru': "Ожидающие активности",
    },
    'lbl_activities_this_month': {
      'uz': "Shu Oydagi Faolliklar",
      'ru': "Активности в этом месяце",
    },
    'lbl_approved_activities': {
      'uz': "Tasdiqlangan Faolliklar",
      'ru': "Подтвержденные активности",
    },
    'lbl_staff_monitoring': {
      'uz': "Xodimlar monitoringi",
      'ru': "Мониторинг сотрудников",
    },
    'lbl_hemis_monitoring': {
      'uz': "HEMIS Monitoring",
      'ru': "Мониторинг HEMIS",
    },
    'lbl_financial_status_2': {
      'uz': "Moliyaviy Holat",
      'ru': "Финансовое состояние",
    },
    'lbl_dormitory_2': {
      'uz': "Turarjoy",
      'ru': "Общежитие",
    },
    'lbl_docs_archive': {
      'uz': "Hujjatlar Arxivi",
      'ru': "Архив документов",
    },
    'lbl_students_2': {
      'uz': "Talabalar",
      'ru': "Студенты",
    },
    'lbl_staff_2': {
      'uz': "Xodimlar",
      'ru': "Сотрудники",
    },
    'lbl_student_portal': {
      'uz': "Student Portal",
      'ru': "Студенческий портал",
    },
    'lbl_student': {
      'uz': "Talaba",
      'ru': "Студент",
    },
    'msg_pass_updated_tick': {
      'uz': "✅ Parol muvaffaqiyatli yangilandi!",
      'ru': "✅ Пароль успешно обновлен!",
    },
    'hint_write_message': {
      'uz': "Xabar yozing...",
      'ru': "Напишите сообщение...",
    },
    'hint_text_or_file': {
      'uz': "Matnni shu yerga yozing yoki fayl yuklang...",
      'ru': "Напишите здесь текст или загрузите файл...",
    },
    'msg_copied': {
      'uz': "Nusxa olindi!",
      'ru': "Скопировано!",
    },
    'lbl_club_name': {
      'uz': "Klub nomi",
      'ru': "Название клуба",
    },
    'hint_tg_channel_link_opt': {
      'uz': "Telegram kanal linki (ixtiyoriy)",
      'ru': "Ссылка на Telegram канал (по желанию)",
    },
    'msg_activity_confirmed': {
      'uz': "Faollik qilib tasdiqlandi!",
      'ru': "Подтверждено как активность!",
    },
    'hint_event_details': {
      'uz': "Tadbir haqida batafsil ma'lumot...",
      'ru': "Подробная информация о мероприятии...",
    },
    'lbl_event_topic': {
      'uz': "Tadbir mavzusi",
      'ru': "Тема мероприятия",
    },
    'hint_book_search': {
      'uz': "Kitob, muallif, janr...",
      'ru': "Книга, автор, жанр...",
    },

        'policy_sec1_title': {
      'uz': "1. UMUMIY QOIDALAR",
      'ru': "1. ОБЩИЕ ПОЛОЖЕНИЯ",
    },
    'policy_sec1_desc': {
      'uz': "Ushbu Maxfiylik Siyosati \"PRIMEWAY GROUP\" MChJ (keyingi o'rinlarda \"Kompaniya\") tomonidan ishlab chiqilgan \"Tengdosh\" platformasi foydalanuvchilarining shaxsiy ma'lumotlarini himoya qilish tartibini belgilaydi.\n\n1.1. Platforma maqsadi: \"Tengdosh\" – bu talabalar, o'qituvchilar va ma'muriyat o'rtasidagi o'quv jarayonini raqamlashtirish va OTM HEMIS tizimi bilan integratsiya qilishga qaratilgan innovatsion ekotizimdir.\n\n1.2. Ilovadan ro'yxatdan o'tish orqali Siz ushbu Siyosat shartlarini to'liq qabul qilgan hisoblanasiz.",
      'ru': "Данная Политика Конфиденциальности определяет порядок защиты персональных данных пользователей платформы «Tengdosh», разработанной ООО «PRIMEWAY GROUP» (далее «Компания»).\n\n1.1. Цель платформы: «Tengdosh» — это инновационная экосистема, направленная на цифровизацию учебного процесса между студентами, преподавателями и администрацией, а также на интеграцию с системой HEMIS вуза.\n\n1.2. Регистрируясь в приложении, вы считаетесь полностью принявшими условия этой Политики.",
    },
    'policy_sec2_title': {
      'uz': "2. YIG'ILADIGAN MA'LUMOTLAR",
      'ru': "2. СОБИРАЕМЫЕ ДАННЫЕ",
    },
    'policy_sec2_desc': {
      'uz': "Biz Sizga xizmat ko'rsatish sifatini oshirish maqsadida quyidagi ma'lumotlarni yig'amiz:\n• Shaxsiy ma'lumotlar: Ism-familiya, telefon raqami, talaba ID (HEMIS ID).\n• Ta'lim ma'lumotlari: Baholar, davomat, dars jadvallari (HEMIS orqali).\n• Texnik ma'lumotlar: IP-manzil, qurilma modeli (xavfsizlik va analitika uchun).",
      'ru': "В целях повышения качества обслуживания мы собираем следующие данные:\n• Личные данные: ФИО, номер телефона, студенческий ID (HEMIS ID).\n• Образовательные данные: Оценки, посещаемость, расписание занятий (через HEMIS).\n• Технические данные: IP-адрес, модель устройства (для безопасности и аналитики).",
    },
    'policy_sec3_title': {
      'uz': "3. PREMIUM XIZMATLAR VA TO'LOVLAR",
      'ru': "3. ПРЕМИУМ УСЛУГИ И ПЛАТЕЖИ",
    },
    'policy_sec3_desc': {
      'uz': "3.1. Platforma ba'zi qo'shimcha imkoniyatlarni (reklamasiz rejim, statistika) \"Premium\" obuna sifatida taklif qilishi mumkin.\n3.2. To'lovlar uchinchi tomon to'lov tizimlari (Payme, Click) orqali amalga oshiriladi. Biz Sizning bank karta ma'lumotlaringizni saqlamaymiz.\n3.3. Qaytarish siyosati: Raqamli xizmatlar ko'rsatilgan hisoblanganligi sababli, Premium obuna uchun to'langan mablag'lar qoida tariqasida qaytarilmaydi.",
      'ru': "3.1. Платформа может предлагать некоторые дополнительные функции (режим без рекламы, статистика) в качестве подписки «Premium».\n3.2. Платежи осуществляются через сторонние платежные системы (Payme, Click). Мы не сохраняем данные вашей банковской карты.\n3.3. Политика возврата: Поскольку электронные услуги считаются оказанными, средства, уплаченные за премиум-подписку, как правило, не подлежат возврату.",
    },
    'policy_sec4_title': {
      'uz': "4. XAVFSIZLIK PROTOKOLLARI",
      'ru': "4. ПРОТОКОЛЫ БЕЗОПАСНОСТИ",
    },
    'policy_sec4_desc': {
      'uz': "Biz Sizning ma'lumotlaringizni himoya qilish uchun ilg'or xalqaro standartlarni qo'llaymiz:\n• Mijoz Tomonida Shifrlash (Client-Side Encryption): Sizning HEMIS parolingiz va sessiya tokenlaringiz bizning serverlarimizda emas, balki faqat Sizning qurilmangiz xotirasida kuchli shifrlangan holda saqlanadi. Serverda faqat vaqtinchalik va shifrlangan ma'lumotlar aylanadi.\n• Action Token System (ATS): Ilova orqali amalga oshiriladigan har bir muhim so'rov (POST) maxsus kriptografik shifr (\"Action Token\") bilan imzolanadi. Bu shifr faqat Sizning qurilmangizda shakllanadi.\n• O'g'rilikdan Himoya: Agar Sizning sessiya kalitingiz (token) o'g'irlangan taqdirda ham, tajovuzkor Sizning nomingizdan biron bir ma'lumotni o'zgartira olmaydi yoki yubora olmaydi, chunki unda qurilmangizga bog'langan maxsus shifr (\"Action Token\") mavjud bo'lmaydi.\n• Security Watchdog: Tizim 24/7 rejimda shubhali harakatlarni kuzatib boradi.",
      'ru': "Мы применяем передовые международные стандарты для защиты ваших данных:\n• Шифрование на стороне клиента (Client-Side Encryption): Ваш пароль HEMIS и токены сессий не хранятся на наших серверах, а сохраняются только в памяти вашего устройства в надежно зашифрованном виде. На сервере циркулируют только временные и зашифрованные данные.\n• Action Token System (ATS): Каждый важный запрос (POST), отправляемый через приложение, подписывается специальным криптографическим шифром («Action Token»). Этот шифр формируется только на вашем устройстве.\n• Защита от кражи: Даже если ваш ключ сессии (токен) украден, злоумышленник не сможет изменить или отправить какие-либо данные от вашего имени, так как у него не будет специального шифра («Action Token»), привязанного к вашему устройству.\n• Security Watchdog: Система в режиме 24/7 контролирует подозрительные действия.",
    },
    'policy_sec5_title': {
      'uz': "5. NIZOLARNI HAL QILISH",
      'ru': "5. РАЗРЕШЕНИЕ СПОРОВ",
    },
    'policy_sec5_desc': {
      'uz': "5.1. Foydalanuvchi va Kompaniya o'rtasidagi nizolar dastlab muzokaralar yo'li bilan hal qilinadi.\n5.2. Agar nizoni 30 kun ichida hal qilish imkoni bo'lmasa, nizo \"PRIMEWAY GROUP\" MChJ joylashgan hududdagi (O'zbekiston Respublikasi) tegishli sudida ko'rib chiqiladi.",
      'ru': "5.1. Споры между Пользователем и Компанией первоначально решаются путем переговоров.\n5.2. Если спор невозможно решить в течение 30 дней, он рассматривается в соответствующем суде на территории (Республика Узбекистан) места нахождения ООО «PRIMEWAY GROUP».",
    },
    'policy_sec6_title': {
      'uz': "6. MA'SULIYATNI CHEKLASH",
      'ru': "6. ОГРАНИЧЕНИЕ ОТВЕТСТВЕННОСТИ",
    },
    'policy_sec6_desc': {
      'uz': "6.1. Kompaniya HEMIS tizimidagi texnik nosozliklar yoki internet provayderlarining aybi bilan yuzaga kelgan uzilishlar uchun javobgar emas.\n6.2. Foydalanuvchi o'z login va paroli xavfsizligi uchun shaxsan javobgardir.",
      'ru': "6.1. Компания не несет ответственности за технические сбои в системе HEMIS или перебои, вызванные по вине интернет-провайдеров.\n6.2. Пользователь лично несет ответственность за безопасность своего логина и пароля.",
    },
    'policy_sec7_title': {
      'uz': "7. BOG'LANISH",
      'ru': "7. КОНТАКТЫ",
    },
    'policy_sec7_desc': {
      'uz': "Savollar va takliflar uchun:\n\"PRIMEWAY GROUP\" MChJ\nEmail: support@tengdosh.uz (yoki ilova ichidagi 'Yordam' bo'limi)",
      'ru': "Для вопросов и предложений:\nООО «PRIMEWAY GROUP»\nEmail: support@tengdosh.uz (или раздел 'Помощь' в приложении)",
    },
    'policy_last_update': {
      'uz': "So'nggi yangilanish: 16-Fevral, 2026-yil",
      'ru': "Последнее обновление: 16 февраля 2026 года",
    },

        'lbl_general_status': {
      'uz': "Umumiy Holat",
      'ru': "Общее состояние",
    },
    'lbl_appeal_lowercase': {
      'uz': "murojaat",
      'ru': "обращение",
    },
    'msg_no_ads_yet': {
      'uz': "Hozircha e'lonlar yo'q",
      'ru': "Пока нет объявлений",
    },
    'lbl_books_clothes_tech': {
      'uz': "Kitoblar, kiyimlar va texnikalar",
      'ru': "Книги, одежда и техника",
    },
    'msg_soon_launch': {
      'uz': "Tez orada ishga tushadi",
      'ru': "Скоро будет запущено",
    },
    'msg_ad_added_successfully': {
      'uz': "E'lon muvaffaqiyatli qo'shildi!",
      'ru': "Объявление успешно добавлено!",
    },
    'msg_no_certs': {
      'uz': "Sertifikatlar yo'q",
      'ru': "Нет сертификатов",
    },
    'msg_cannot_open_tg': {
      'uz': "Telegramni ochib bo'lmadi",
      'ru': "Не удалось открыть Telegram",
    },
    'msg_my_tg_is_new': {
      'uz': "Telegramim yangi",
      'ru': "Мой Telegram новый",
    },
    'lbl_groups_list': {
      'uz': "Guruhlar ro'yxati",
      'ru': "Список групп",
    },
    'msg_no_assigned_groups': {
      'uz': "Sizga biriktirilgan guruhlar yo'q",
      'ru': "У вас нет прикрепленных групп",
    },
    'lbl_active_students': {
      'uz': "Faol Talabalar",
      'ru': "Активные студенты",
    },
    'lbl_not_uploaded': {
      'uz': "Yuklamagan",
      'ru': "Не загружено",
    },
    'lbl_uploaded': {
      'uz': "Yuklagan",
      'ru': "Загружено",
    },
    'lbl_status': {
      'uz': "Holati",
      'ru': "Статус",
    },
    'msg_no_new_appeals': {
      'uz': "Yangi murojaatlar yo'q",
      'ru': "Нет новых обращений",
    },
    'lbl_image_available': {
      'uz': "Rasm mavjud",
      'ru': "Есть фото",
    },
    'lbl_discussion': {
      'uz': "Muhokama",
      'ru': "Обсуждение",
    },
    'btn_delete_chat': {
      'uz': "Chatni o'chirish",
      'ru': "Удалить чат",
    },
    'msg_no_messages': {
      'uz': "Xabarlar yo'q",
      'ru': "Нет сообщений",
    },
    'lbl_teahouse': {
      'uz': "Choyxona",
      'ru': "Чайхана",
    },
    'lbl_my_direction': {
      'uz': "Mening yo'nalishim",
      'ru': "Мое направление",
    },
    'lbl_all_directions': {
      'uz': "Barcha yo'nalishlar",
      'ru': "Все направления",
    },
    'msg_username_length_err': {
      'uz': "Username 2-25 belgi bo'lishi kerak",
      'ru': "Username должен содержать от 2 до 25 символов",
    },
    'btn_write_message': {
      'uz': "Xabar yozish",
      'ru': "Написать сообщение",
    },
    'msg_no_posts': {
      'uz': "Postlar yo'q",
      'ru': "Нет постов",
    },
    'msg_no_reposts': {
      'uz': "Repostlar yo'q",
      'ru': "Нет репостов",
    },
    'btn_delete_message': {
      'uz': "Xabarni o'chirish",
      'ru': "Удалить сообщение",
    },
    'lbl_replying': {
      'uz': "Javob berilmoqda",
      'ru': "Отвечает",
    },
    'msg_del_error': {
      'uz': "O'chirishda xatolik",
      'ru': "Ошибка при удалении",
    },
    'btn_publish': {
      'uz': "CHOP ETISH",
      'ru': "ОПУБЛИКОВАТЬ",
    },
    'btn_add_variant': {
      'uz': "Variant qo'shish",
      'ru': "Добавить вариант",
    },
    'msg_confirm_delete_post': {
      'uz': "Haqiqatan ham bu postni o'chirmoqchimisiz?",
      'ru': "Вы действительно хотите удалить этот пост?",
    },
    'btn_copy_link': {
      'uz': "Linkdan nusxa olish",
      'ru': "Скопировать ссылку",
    },
    'msg_link_copied': {
      'uz': "Link buferga nusxalandi!",
      'ru': "Ссылка скопирована в буфер обмена!",
    },
    'btn_read_less': {
      'uz': "Kamroq o'qish",
      'ru': "Читать меньше",
    },
    'btn_read_more': {
      'uz': "Davomi",
      'ru': "Продолжение",
    },
    'msg_search_hint_user': {
      'uz': "Username yoki ism kiriting\n(kamida 2 ta harf)",
      'ru': "Введите Username или имя\n(минимум 2 буквы)",
    },
    'msg_edit_err': {
      'uz': "Tahrirlashda xatolik bo'ldi",
      'ru': "Ошибка при редактировании",
    },
    'msg_del_err_2': {
      'uz': "O'chirishda xatolik bo'ldi",
      'ru': "Ошибка при удалении",
    },
    'msg_unsaved_changes': {
      'uz': "Saqlanmagan o'zgarishlar",
      'ru': "Несохраненные изменения",
    },
    'btn_stay': {
      'uz': "Qolish",
      'ru': "Остаться",
    },
    'msg_format_menu_soon': {
      'uz': "Formatlash menyusi (Tez orada)",
      'ru': "Меню форматирования (Скоро)",
    },
    'msg_waiting_for_reply': {
      'uz': "Javob kutilmoqda...",
      'ru': "Ожидание ответа...",
    },
    'msg_name_kept_secret': {
      'uz': "Ismingiz sir saqlanadi",
      'ru': "Ваше имя будет скрыто",
    },
    'btn_attach_file_tg': {
      'uz': "Fayl biriktirish (Telegram)",
      'ru': "Прикрепить файл (Telegram)",
    },
    'lbl_send_media': {
      'uz': "Rasm, video yoki PDF yuborish",
      'ru': "Отправить фото, видео или PDF",
    },
    'msg_survey_success': {
      'uz': "So'rovnoma muvaffaqiyatli yakunlandi!",
      'ru': "Опрос успешно завершен!",
    },
    'msg_pwd_length_err': {
      'uz': "Parol kamida 6 belgidan iborat bo'lishi kerak",
      'ru': "Пароль должен состоять минимум из 6 символов",
    },
    'lbl_subject_data': {
      'uz': "Fan Ma'lumotlari",
      'ru': "Данные предмета",
    },
    'lbl_candidate_program': {
      'uz': "Nomzod dasturi",
      'ru': "Программа кандидата",
    },
    'lbl_candidates_list': {
      'uz': "Nomzodlar ro'yxati",
      'ru': "Список кандидатов",
    },
    'msg_contract_data_not_found': {
      'uz': "Shartnoma ma'lumotlari topilmadi",
      'ru': "Данные договора не найдены",
    },
    'lbl_status_colon': {
      'uz': "Holat:",
      'ru': "Статус:",
    },
    'lbl_finance_summary': {
      'uz': "Moliya xulosasi",
      'ru': "Финансовый отчет",
    },
    'lbl_income': {
      'uz': "Kirim",
      'ru': "Приход",
    },
    'lbl_subjects_and_resources': {
      'uz': "Fanlar va Resurslar",
      'ru': "Предметы и ресурсы",
    },
    'lbl_rent_subsidy': {
      'uz': "Ijara Subsidiyasi",
      'ru': "Субсидия на аренду",
    },
    'btn_delete_doc': {
      'uz': "Hujjatni o'chirish",
      'ru': "Удалить документ",
    },
    'msg_buy_plan_confirm': {
      'uz': "Siz quyidagi tarifni sotib olmoqchimisiz?",
      'ru': "Вы хотите купить следующий тариф?",
    },
    'lbl_premium_subscription': {
      'uz': "Premium obuna",
      'ru': "Премиум подписка",
    },
    'lbl_tariffs': {
      'uz': "Tariflar:",
      'ru': "Тарифы:",
    },
    'lbl_use_all_features_unlimited': {
      'uz': "Barcha imkoniyatlardan cheklovsiz foydalaning",
      'ru': "Пользуйтесь всеми возможностями без ограничений",
    },
    'lbl_your_balance': {
      'uz': "Sizning balansingiz",
      'ru': "Ваш баланс",
    },
    'msg_one_week_trial': {
      'uz': "Bir haftalik bepul sinov davri!",
      'ru': "Недельный бесплатный пробный период!",
    },
    'btn_start_now': {
      'uz': "Hozir boshlash",
      'ru': "Начать сейчас",
    },
    'msg_student_data_not_found': {
      'uz': "Talaba ma'lumotlari topilmadi",
      'ru': "Данные студента не найдены",
    },
    'lbl_choose_status_icon': {
      'uz': "Status Belgisini Tanlang",
      'ru': "Выберите значок статуса",
    },
    'btn_delete_account': {
      'uz': "Hisobni o'chirish",
      'ru': "Удалить аккаунт",
    },
    'msg_account_deleted_success': {
      'uz': "Hisobingiz muvaffaqiyatli o'chirildi",
      'ru': "Ваш аккаунт успешно удален",
    },
    'lbl_active_election': {
      'uz': "Faol saylov!",
      'ru': "Активные выборы!",
    },
    'msg_no_staff_found': {
      'uz': "Xodimlar topilmadi",
      'ru': "Сотрудники не найдены",
    },
    'lbl_student_data': {
      'uz': "Talaba ma'lumotlari",
      'ru': "Данные студента",
    },
    'lbl_living': {
      'uz': "Yashamoqda",
      'ru': "Проживает",
    },
    'lbl_platform_activity': {
      'uz': "Platforma aktivligi",
      'ru': "Активность платформы",
    },
    'msg_u_can_upload_more_bot': {
      'uz': "Yana yuklashingiz mumkin (Bot orqali)",
      'ru': "Вы можете загрузить еще (через Бот)",
    },
    'msg_press_btn_send_img': {
      'uz': "Tugmani bosing va Botga rasm yuboring",
      'ru': "Нажмите кнопку и отправьте фото в Бот",
    },
    'lbl_social_activity': {
      'uz': "Ijtimoiy Faollik",
      'ru': "Социальная активность",
    },
    'btn_add_activity': {
      'uz': "Faollik qo'shish",
      'ru': "Добавить активность",
    },
    'msg_confirm_delete_activity': {
      'uz': "Haqiqatan ham ushbu faollikni o'chirmoqchimisiz?",
      'ru': "Вы действительно хотите удалить эту активность?",
    },
    'msg_deleted': {
      'uz': "O'chirildi!",
      'ru': "Удалено!",
    },
    'lbl_club_activities_events': {
      'uz': "Klubdagi faolliklari (Tadbirlar)",
      'ru': "Активности в клубе (Мероприятия)",
    },
    'msg_no_activities_yet': {
      'uz': "Hozircha faollik yo'q",
      'ru': "Пока нет активностей",
    },
    'btn_add_club': {
      'uz': "Klub qo'shish",
      'ru': "Добавить клуб",
    },
    'btn_edit_club': {
      'uz': "Klubni tahrirlash",
      'ru': "Редактировать клуб",
    },
    'btn_join_club': {
      'uz': "Klubga a'zo bo'lish",
      'ru': "Вступить в клуб",
    },
    'lbl_university_club': {
      'uz': "Universitet Klubi",
      'ru': "Университетский клуб",
    },
    'msg_event_loc_time_not_entered': {
      'uz': "Tadbir manzili / vaqti kiritilmagan",
      'ru': "Адрес / время мероприятия не указаны",
    },
    'msg_club_created_success': {
      'uz': "Klub muvaffaqiyatli yaratildi!",
      'ru': "Клуб успешно создан!",
    },
    'btn_activate_premium': {
      'uz': "Premium-ni faollashtirish",
      'ru': "Активировать Премиум",
    },
    'msg_all_copies_busy': {
      'uz': "Hozirda barcha nusxalar band. Navbatga yozilsangiz, kitob qaytishi bilan sizga habar beramiz.",
      'ru': "На данный момент все экземпляры заняты. Если вы запишетесь в очередь, мы сообщим, как только книга вернется.",
    },
    'lbl_sorting': {
      'uz': "Saralash",
      'ru': "Сортировка",
    },
    'lbl_filter': {
      'uz': "Filtr",
      'ru': "Фильтр",
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
    final localeProvider = Provider.of<LocaleProvider>(context, listen: false);
    final langCode = localeProvider.locale.languageCode;
    
    final node = strings[key];
    if (node == null) return key; // Fallback to key if not found
    
    return node[langCode] ?? node['uz'] ?? key;
  }
}
