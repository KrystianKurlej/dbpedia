# Dokumentacja Aplikacji: DBpedia Person Search & Graph Viewer

## 1. Wprowadzenie

Aplikacja została zaprojektowana jako interaktywne narzędzie umożliwiające przeszukiwanie bazy wiedzy DBpedia w celu znalezienia osób na podstawie wpisanego imienia lub nazwiska. Po wybraniu konkretnej osoby użytkownik może wygenerować graficzny graf wiedzy, który przedstawia powiązania tej osoby z innymi encjami (osobami, miejscami, wydarzeniami itd.).

Całość została zbudowana z wykorzystaniem frameworka Flask, biblioteki SPARQLWrapper do wykonywania zapytań SPARQL, oraz narzędzi NetworkX i Pyvis do konstrukcji oraz wizualizacji grafów.

## 2. Jak działa aplikacja (krok po kroku)

1. Użytkownik wprowadza nazwę osoby w formularzu na stronie głównej.
2. Aplikacja wykonuje zapytanie SPARQL do endpointu DBpedia, szukając osób, których etykiety pasują do podanej nazwy.
3. Wyniki są sortowane z użyciem algorytmu fuzzy matchingu (RapidFuzz), by uwzględniać błędy i dopasowania częściowe.
4. Jeśli znaleziono dopasowania, wyświetlana jest lista z linkami.
5. Po kliknięciu w link, aplikacja buduje graf wiedzy wokół wybranej osoby (maksymalnie 2 poziomy głębokości).
6. Graf jest renderowany przy pomocy Pyvis jako interaktywny HTML.
7. Użytkownik może klikać w węzły grafu, by uzyskać opis danej encji z DBpedia.
8. Aplikacja wyświetla komunikaty w przypadku błędów lub pustych wyników.

## 3. Opis wszystkich funkcji

- `index()`: Obsługuje stronę główną. Przetwarza formularz, wykonuje zapytanie i renderuje wyniki lub komunikat błędu.
- `details()`: Pobiera URI osoby, buduje graf wiedzy, renderuje go i zwraca w HTML.
- `node_description()`: Zwraca JSON z opisem (abstract) encji po kliknięciu w węzeł grafu.
- `query_dbpedia_for_person_fuzzy(name)`: Wysyła zapytanie do DBpedia, filtruje osoby, stosuje fuzzy matching i zwraca wyniki.
- `query_dbpedia_relations_with_types(resource_uri)`: Pobiera relacje RDF i klasyfikuje typy encji (osoba, miejsce, itd.).
- `build_knowledge_graph(root_uri, root_label)`: Tworzy graf wiedzy do maksymalnie 2 poziomów, ogranicza liczbę węzłów.
- `generate_pyvis_graph(G, physics=True)`: Renderuje interaktywny graf HTML z kolorowaniem węzłów.

## 4. Technologie i biblioteki

- **Flask** – backend webowy  
- **SPARQLWrapper** – zapytania SPARQL do DBpedia  
- **Pyvis** – wizualizacja grafu w przeglądarce  
- **NetworkX** – struktura grafu w Pythonie  
- **RapidFuzz** – fuzzy matching (dopasowanie nazw)  
- **HTML / JS** – frontend i interaktywność

## 5. Mocne strony

- Prosta i przejrzysta obsługa.
- Interaktywna wizualizacja grafów.
- Fuzzy matching pozwala na elastyczne wyszukiwanie.
- Dynamiczne opisy encji z DBpedia.

## 6. Słabe strony

- DBpedia zawiera niekompletne lub nieaktualne dane.
- Nie każda encja ma opis ani ranking.
- Wydajność może być problematyczna przy ogólnych hasłach.
- Brak paginacji dla dużej liczby wyników.
- Fuzzy matching może pomijać trafne wyniki, jeśli mają niskie dopasowanie.

## 7. Uwagi końcowe

Choć DBpedia jest szeroko znaną i otwartą bazą wiedzy RDF, jej dane są często niekompletne, a aktualność może być ograniczona. Aplikacja najlepiej sprawdza się dla znanych osób (np. Albert Einstein), natomiast słabiej radzi sobie z mniej znanymi encjami lub nienazwanymi precyzyjnie. Niemniej jednak, prezentowana aplikacja jest dobrym punktem wyjścia do eksploracji danych semantycznych i tworzenia interaktywnych narzędzi wizualizacyjnych.