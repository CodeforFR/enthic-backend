LOAD DATA INFILE "/var/lib/mysql/identity.csv"
IGNORE INTO TABLE identity
COLUMNS TERMINATED BY '\t'
LINES TERMINATED BY '\n';
