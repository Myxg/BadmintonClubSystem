mv /mbackups/today.sql /mbackups/old.sql
mysqldump -uroot -pHbts@1234 --single-transaction --master-data=2 --triggers -f -R -E --hex-blob --databases club> /mbackups/today.sql
date
