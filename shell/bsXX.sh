cat bsXX.things |sed s/bs01/$1/g | sed s/a4c138dd5b08/$2/g > ../things/$1.things
cat thing-bsXX.items |sed s/bs01/$1/g | sed s/a4c138dd5b08/$2/g > ../items/thing-$1.items
chown openhab. ../things/$1.things ../items/thing-$1.items
