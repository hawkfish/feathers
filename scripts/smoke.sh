# !/bin/sh
git grep -E -w -i $1 -- '*.test' | egrep -v ':#' | cut -d ':' -f 1 | uniq > smoke.test
git grep -E -w -i $1 --  '*.test_*' | egrep -v ':#' | cut -d ':' -f 1 | uniq > smoke.test_slow
cat smoke.test smoke.test_slow | wc -l

