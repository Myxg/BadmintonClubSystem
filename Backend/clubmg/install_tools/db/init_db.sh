#!/bin/bash
#
# 初始化 db 和表结构
#

host="127.0.0.1"
user="root"
password="Hbts@1234"

tables="
club.sql
club_user_exp.sql
club_history_data.sql
club_physical_fitness_items.sql
club_operation.sql
club_permission.sql
club_operation_permission.sql
"

mysql -h"$host" -u"$user" -p"$password" -e "DROP database IF EXISTS \`club\`; CREATE DATABASE \`club\` DEFAULT CHARACTER SET utf8;"

for t in $tables
do
    mysql -h"$host" -u"$user" -p"$password" club < ./$t
done

