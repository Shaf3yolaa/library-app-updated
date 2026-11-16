USE library;
SELECT b.book_id,
       b.title,
       b.price,
       b.publish_year,
       a.name AS author,
       p.name AS publisher,
       c.name AS category
FROM BOOK b
     JOIN AUTHOR a    ON a.author_id = b.author_id
     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id
     JOIN CATEGORY c  ON c.category_id = b.category_id
WHERE b.title LIKE '%Murder%'
  AND b.price BETWEEN 15 AND 30
  AND b.category_id = 2
ORDER BY b.price ASC, b.title ASC;
--
SET @keyword     = '%Murder%';
SET @min_price   = 15;
SET @max_price   = 30;
SET @category_id = 2;

PREPARE search_books FROM
'SELECT b.book_id,
        b.title,
        b.price,
        b.publish_year,
        a.name AS author,
        p.name AS publisher,
        c.name AS category
 FROM BOOK b
      JOIN AUTHOR a    ON a.author_id = b.author_id
      JOIN PUBLISHER p ON p.publisher_id = b.publisher_id
      JOIN CATEGORY c  ON c.category_id = b.category_id
 WHERE b.title LIKE ?
   AND b.price BETWEEN ? AND ?
   AND b.category_id = ?
 ORDER BY b.price ASC, b.title ASC';

EXECUTE search_books USING @keyword, @min_price, @max_price, @category_id;
DEALLOCATE PREPARE search_books;

--
SELECT b.book_id,
       b.title,
       a.name AS author,
       p.name AS publisher,
       c.name AS category,
       b.price,
       b.publish_year
FROM BOOK b
     JOIN AUTHOR a    ON a.author_id = b.author_id
     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id
     JOIN CATEGORY c  ON c.category_id = b.category_id
ORDER BY a.name ASC, b.title ASC;

-- 
SELECT c.category_id,
       c.name        AS category,
       COUNT(b.book_id)  AS number_of_books,
       ROUND(AVG(b.price), 2) AS average_price
FROM CATEGORY c
     JOIN BOOK b ON b.category_id = c.category_id
GROUP BY c.category_id, c.name
ORDER BY number_of_books DESC, category ASC;

--
SELECT a.author_id,
       a.name AS author,
       COUNT(b.book_id) AS number_of_books
FROM AUTHOR a
     JOIN BOOK b ON b.author_id = a.author_id
GROUP BY a.author_id, a.name
HAVING COUNT(b.book_id) >= 2
ORDER BY number_of_books DESC, author ASC;

-- 
SELECT COUNT(book_id) AS number_of_books,
       SUM(price)     AS total_price,
       MIN(price)     AS smallest_price,
       MAX(price)     AS largest_price
FROM BOOK;

-- 
SELECT l.loan_id,
       b.title  AS book,
       m.name   AS member,
       l.loan_date
FROM LOAN l
     JOIN BOOK b   ON b.book_id = l.book_id
     JOIN MEMBER m ON m.member_id = l.member_id
WHERE l.return_date IS NULL
ORDER BY l.loan_date ASC;

-- 
SELECT m.member_id,
       m.name,
       m.email,
       m.join_date
FROM MEMBER m
     LEFT JOIN LOAN l ON l.member_id = m.member_id
WHERE l.loan_id IS NULL
ORDER BY m.name ASC;

--
SELECT b.book_id,
       b.title,
       a.name AS author,
       b.price
FROM BOOK b
     JOIN AUTHOR a ON a.author_id = b.author_id
     LEFT JOIN LOAN l ON l.book_id = b.book_id
WHERE l.loan_id IS NULL
ORDER BY b.title ASC;

--
SELECT b.book_id,
       b.title,
       COUNT(l.loan_id) AS number_of_loans
FROM BOOK b
     JOIN LOAN l ON l.book_id = b.book_id
GROUP BY b.book_id, b.title
ORDER BY number_of_loans DESC, b.title ASC
LIMIT 3;

--
SELECT m.member_id,
       m.name AS member,
       COUNT(l.loan_id) AS number_of_loans
FROM MEMBER m
     JOIN LOAN l ON l.member_id = m.member_id
GROUP BY m.member_id, m.name
ORDER BY number_of_loans DESC, member ASC
LIMIT 1;

--
SELECT a.author_id,
       a.name AS author,
       a.country,
       COUNT(b.book_id) AS number_of_books
FROM AUTHOR a
     LEFT JOIN BOOK b ON b.author_id = a.author_id
GROUP BY a.author_id, a.name, a.country
ORDER BY number_of_books DESC, author ASC;

--
SELECT b.book_id,
       b.title,
       a.name AS author,
       a.country AS author_country,
       p.name AS publisher,
       p.country AS publisher_country
FROM BOOK b
     JOIN AUTHOR a    ON a.author_id = b.author_id
     JOIN PUBLISHER p ON p.publisher_id = b.publisher_id
WHERE a.country = p.country
ORDER BY b.title ASC;
