## RusY: Видеохостинг на базе Flask и PostgreSQL

RusY - это масштабный проект, представляющий собой упрощенную версию YouTube, реализованную на базе фреймворка Flask и системы управления базами данных PostgreSQL.

## Ключевые особенности:
- Регистрация пользователей: Пользователи могут регистрироваться на платформе, автоматически создавая свой канал.
![image](https://github.com/user-attachments/assets/101ae5eb-d80f-43fa-8ab5-62bda1fdf10d)
![image](https://github.com/user-attachments/assets/ffa97baf-843d-4716-b84d-493740f16ba2)
![image](https://github.com/user-attachments/assets/a9e36c22-5599-456e-86de-1cee9d6d60f3)
![image](https://github.com/user-attachments/assets/1b37532e-197b-4073-beae-954f3abd6f8b)

- Загрузка видео: Пользователи могут загружать видео на свои каналы, и они автоматически появляются на главной странице (с видео всех каналов), а также в быстром поиске по выбранной категории.

![image](https://github.com/user-attachments/assets/e2b6f472-ea90-45d4-8d9b-4e7e958666b7)
![image](https://github.com/user-attachments/assets/1d65096e-3966-402c-ac99-93b939b4d29c)
![image](https://github.com/user-attachments/assets/4d1f3e29-73fe-4da0-ada2-fefe8db24c44)
![image](https://github.com/user-attachments/assets/f29ac05c-794d-4a33-a9c6-081b940dea90)

- Взаимодействие: Пользователи могут оставлять комментарии, ставить лайки и дизлайки к видео. Поставленные лайки добавляют видео во вкладку “Понравившиеся”. Видео с более чем 6 лайками попадают в категорию “Популярные”.

![image](https://github.com/user-attachments/assets/c7de36c9-6162-4ad9-abd7-b6507b547d39)
![image](https://github.com/user-attachments/assets/b851f982-e2e0-4497-9980-7ca7a3f3854c)

- Управление контентом: Пользователи могут редактировать и удалять свои видео и профили. При удалении видео из базы данных удаляются все комментарии и отметки.

![image](https://github.com/user-attachments/assets/b728b350-b392-4979-98be-f7760e38d677)
![image](https://github.com/user-attachments/assets/472bfb98-6c91-4fed-86b6-77b287565950)
![image](https://github.com/user-attachments/assets/e41ab057-adce-4c21-9ea7-0170a9d02d01)

- Подписки: Пользователи могут подписываться на каналы других пользователей. Подписанные каналы попадают в категорию “Подписки”.

![image](https://github.com/user-attachments/assets/b367cad0-e953-42be-8222-6a8a8711edbf)
![image](https://github.com/user-attachments/assets/4b5ce75d-1b4b-4c89-a457-4beed541c812)

## Технологии:

- Flask: Веб-фреймворк Python, используемый для создания веб-приложения RusY.
- PostgreSQL: Система управления базами данных, используемая для хранения всех данных RusY, включая видео, комментарии, профили и т.д.

## Дополнительные возможности:

- Поиск: Реализация более сложного поиска с поддержкой фильтров и сортировки.
