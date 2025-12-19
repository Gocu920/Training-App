# Training App

## Opis projektu

Aplikacja Training App służy do zarządzania treningami. Umożliwia trenerom tworzenie i przypisywanie treningów dla zawodników oraz przeglądanie wyników. 

## Zawartość bazy danych

W bazie danych znajdują się już utworzeni użytkownicy. Aby zalogować się do profilu zawodnika, można użyć poniższych danych:

- **Login:** `A_zawodnik`
- **Hasło:** `Haslo123`

Aby zalogować się do profilu trenera, można użyć poniższych danych:

- **Login:** `A_trener`
- **Hasło:** `Haslo123`

## Generowanie danych

Aby wygenerować nowe dane, należy najpierw usunąć wszystkie istniejące treningi i użytkowników z bazy danych. Można to zrobić przy użyciu panelu admina.


1. Zaloguj się do panelu admina.
2. Usuń wszystkie wpisy w modelach `Training` i `User`.

Następnie należy uruchomić poniższą komende w katalogu głównym projektu

python manage.py generate_data

Autorzy projektu: Wojciech Damian, Mateusz Goc
