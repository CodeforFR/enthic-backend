SELECT * FROM bundle
INTO OUTFILE '/home/BDDexport/bundle-export.csv'
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
SELECT * FROM annual_statistics
INTO OUTFILE '/home/BDDexport/annual_statistics-export.csv'
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
SELECT * FROM identity
INTO OUTFILE '/home/BDDexport/identity-export.csv'
FIELDS TERMINATED BY ';'
ENCLOSED BY '"'
LINES TERMINATED BY '\n';
