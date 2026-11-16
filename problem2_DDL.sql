DROP DATABASE IF EXISTS library;
CREATE DATABASE library;
USE library;
CREATE TABLE AUTHOR (
    author_id  INT          NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    country    VARCHAR(100) NOT NULL,
    image_path VARCHAR(255) NULL, 
    PRIMARY KEY (author_id)
);
CREATE TABLE PUBLISHER (
    publisher_id INT          NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    country      VARCHAR(100) NOT NULL,
    PRIMARY KEY (publisher_id)
);
CREATE TABLE CATEGORY (
    category_id INT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    PRIMARY KEY (category_id)
) ENGINE = InnoDB;
CREATE TABLE BOOK (
    book_id      INT           NOT NULL AUTO_INCREMENT,
    title        VARCHAR(150)  NOT NULL,
    price        DECIMAL(10,2) NOT NULL,
    publish_year YEAR          NOT NULL,
    author_id    INT           NOT NULL,
    publisher_id INT           NOT NULL,
    category_id  INT           NOT NULL,
    image_path   VARCHAR(255)  NULL,    
    PRIMARY KEY (book_id),
    CONSTRAINT fk_book_author
        FOREIGN KEY (author_id)    REFERENCES AUTHOR (author_id)       ON DELETE CASCADE,
    CONSTRAINT fk_book_publisher
        FOREIGN KEY (publisher_id) REFERENCES PUBLISHER (publisher_id),
    CONSTRAINT fk_book_category
        FOREIGN KEY (category_id)  REFERENCES CATEGORY (category_id)
);

CREATE TABLE MEMBER (
    member_id INT          NOT NULL AUTO_INCREMENT,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(255) NOT NULL,
    join_date DATE         NOT NULL,
    PRIMARY KEY (member_id),
    UNIQUE (email)
);

CREATE TABLE LOAN (
    loan_id     INT  NOT NULL AUTO_INCREMENT,
    book_id     INT  NOT NULL,
    member_id   INT  NOT NULL,
    loan_date   DATE NOT NULL,
    return_date DATE NULL,
    PRIMARY KEY (loan_id),
    CONSTRAINT fk_loan_book
        FOREIGN KEY (book_id)   REFERENCES BOOK (book_id)     ON DELETE CASCADE,
    CONSTRAINT fk_loan_member
        FOREIGN KEY (member_id) REFERENCES MEMBER (member_id) ON DELETE CASCADE
);
CREATE TABLE users (
    user_id           INT          NOT NULL AUTO_INCREMENT,
    email             VARCHAR(255) NOT NULL,
    name              VARCHAR(100) NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE (email)
);