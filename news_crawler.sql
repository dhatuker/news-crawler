-- phpMyAdmin SQL Dump
-- version 4.8.4
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 16, 2020 at 02:37 PM
-- Server version: 10.1.37-MariaDB
-- PHP Version: 7.3.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `news_crawler`
--

-- --------------------------------------------------------

--
-- Table structure for table `content_table`
--

CREATE TABLE `content_table` (
  `news_id` int(3) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `content` varchar(10000) DEFAULT NULL,
  `tgl_terbit` date DEFAULT NULL,
  `total_share` int(9) DEFAULT NULL,
  `total_comment` int(9) DEFAULT NULL,
  `editor` varchar(30) DEFAULT NULL,
  `link` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `sumber_berita`
--

CREATE TABLE `sumber_berita` (
  `id` int(3) NOT NULL,
  `link_sumber` varchar(255) DEFAULT NULL,
  `recompile` varchar(30) DEFAULT NULL,
  `title_tag` varchar(10) DEFAULT NULL,
  `title_class` varchar(30) DEFAULT NULL,
  `date_tag` varchar(10) DEFAULT NULL,
  `date_class` varchar(30) DEFAULT NULL,
  `editor_tag` varchar(10) DEFAULT NULL,
  `editor_class` varchar(30) DEFAULT NULL,
  `newscontent_tag` varchar(10) DEFAULT NULL,
  `newscontent_class` varchar(30) DEFAULT NULL,
  `page_tag` varchar(10) DEFAULT NULL,
  `page_class` varchar(30) DEFAULT NULL,
  `share_tag` varchar(10) DEFAULT NULL,
  `share_class` varchar(30) DEFAULT NULL,
  `iframe_comment` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `sumber_berita`
--

INSERT INTO `sumber_berita` (`id`, `link_sumber`, `recompile`, `title_tag`, `title_class`, `date_tag`, `date_class`, `editor_tag`, `editor_class`, `newscontent_tag`, `newscontent_class`, `page_tag`, `page_class`, `share_tag`, `share_class`, `iframe_comment`) VALUES
(1, 'https://www.krjogja.com/berita-terkini/', '^https://', 'h1', 'single-header__title', 'div', 'post-date', 'div', 'editor', 'div', 'content', 'div', 'pagination', NULL, NULL, './/iframe[@class=\"i-amphtml-fill-content\"]'),
(2, 'https://www.todayonline.com/singapore', '^/singapore/', 'h1', 'article-detail_title', 'div', 'article-detail_bylinepublish', 'span', 'today-author', 'div', 'article-detail_body', NULL, NULL, 'p', 'share-count-common', NULL);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `content_table`
--
ALTER TABLE `content_table`
  ADD PRIMARY KEY (`title`),
  ADD KEY `news_id` (`news_id`);

--
-- Indexes for table `sumber_berita`
--
ALTER TABLE `sumber_berita`
  ADD PRIMARY KEY (`id`);

--
-- Constraints for dumped tables
--

--
-- Constraints for table `content_table`
--
ALTER TABLE `content_table`
  ADD CONSTRAINT `content_table_ibfk_1` FOREIGN KEY (`news_id`) REFERENCES `sumber_berita` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
