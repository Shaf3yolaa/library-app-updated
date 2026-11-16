USE library;

INSERT INTO AUTHOR (author_id, name, country) VALUES
(1, 'Naguib Mahfouz', 'Egypt'),
(2, 'Agatha Christie', 'United Kingdom'),
(3, 'Taha Hussein', 'Egypt'),
(4, 'Orhan Pamuk', 'Turkey'),
(5, 'Ahdaf Soueif', 'Egypt');

INSERT INTO PUBLISHER (publisher_id, name, country) VALUES
(1, 'Penguin Books', 'United Kingdom'),
(2, 'Dar El-Shorouk', 'Egypt'),
(3, 'Vintage Books', 'United States'),
(4, 'Can Yayinlari', 'Turkey');

INSERT INTO CATEGORY (category_id, name) VALUES
(1, 'Novel'),
(2, 'Mystery'),
(3, 'Memoir'),
(4, 'Short Stories');

INSERT INTO BOOK (book_id, title, price, publish_year, author_id, publisher_id, category_id) VALUES
( 1, 'Palace Walk',                     45.00, 1956, 1, 2, 1),
( 2, 'Children of the Alley',           32.50, 1959, 1, 2, 1),
( 3, 'The Harafish',                    27.00, 1977, 1, 2, 1),
( 4, 'The Thief and the Dogs',          15.75, 1961, 1, 2, 1),
( 5, 'Murder on the Orient Express',    25.00, 1934, 2, 1, 2),
( 6, 'And Then There Were None',        28.00, 1939, 2, 1, 2),
( 7, 'The Murder of Roger Ackroyd',     19.50, 1926, 2, 1, 2),
( 8, 'The Days',                        18.00, 1929, 3, 2, 3),
( 9, 'The Call of the Curlew',          20.50, 1934, 3, 2, 4),
(10, 'The Tree of Misery',              24.00, 1944, 3, 2, 1),
(11, 'The Map of Love',                 22.00, 1999, 5, 1, 1),
(12, 'Aisha',                           16.75, 1983, 5, 3, 4);

INSERT INTO MEMBER (member_id, name, email, join_date) VALUES
(1, 'Ahmed Elshafeey',   'ahmed.elshafeey@example.com', '2024-09-01'),
(2, 'Mona Abdelrahman',  'mona.abdelrahman@example.com', '2024-10-15'),
(3, 'Youssef Kamal',     'youssef.kamal@example.com',    '2025-01-20'),
(4, 'Salma Fathy',       'salma.fathy@example.com',      '2025-03-05'),
(5, 'Omar Hassan',       'omar.hassan@example.com',      '2025-05-11'),
(6, 'Nour Ibrahim',      'nour.ibrahim@example.com',     '2025-08-02');

INSERT INTO LOAN (loan_id, book_id, member_id, loan_date, return_date) VALUES
( 1,  1, 1, '2025-09-01', '2025-09-15'),
( 2,  4, 2, '2025-09-03', '2025-09-20'),
( 3,  5, 1, '2025-09-10', '2025-09-24'),
( 4,  1, 3, '2025-09-12', '2025-10-01'),
( 5,  2, 4, '2025-09-20', '2025-10-05'),
( 6,  6, 2, '2025-10-01', '2025-10-18'),
( 7,  7, 5, '2025-10-04', NULL),
( 8,  8, 3, '2025-10-06', '2025-10-20'),
( 9,  1, 5, '2025-10-10', NULL),
(10,  9, 4, '2025-10-12', '2025-10-30'),
(11,  5, 1, '2025-10-18', '2025-11-02'),
(12,  3, 2, '2025-10-22', '2025-11-05'),
(13,  1, 2, '2025-11-01', NULL),
(14,  4, 4, '2025-11-08', '2025-11-15');