odesk-podatki
=============

A utility for computing Polish taxes for incomes from Odesk.

Pobierz pliki CSV z https://www.odesk.com/earnings-history/ i zapisz je w katalogu z odesk-podatki.
Jeżeli potrzeba, pobierz tabele średnich kursów ze strony NBP: http://www.nbp.pl/home.aspx?c=/ascx/archa.ascx i zapisz je do folderu nbp.

Utwórz plik kraje.csv zawierający kraj pochodzenia twoich klientów, np:
```
Foo company,US
Bar company,US
Hallöchen Gmbh,Niemcy
```

Utwórz plik zaliczki.csv w którym będziesz zapisywał zaliczki, które już zapłaciłeś, np:
```
2014,1,500
2014,2,300
```
Oznacza, że w styczki zapłaciłeś 500 zł zaliczki, a w lutym 300 zł.

Zainstaluj zależności:
```
pip3 install xlrd python-dateutil
```

Uruchom program:

```
python3 process.py
```
