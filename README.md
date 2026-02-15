# CoAP Remote Storage Server
proiectrcp2025-secure-shell created by GitHub Classroom

# Descriere generală
Acest proiect implementează un server CoAP (Constrained Application Protocol) capabil să gestioneze cereri provenite de la un client într-un sistem de tip remote storage. Comunicarea se face prin socket-uri UDP, conform specificațiilor din RFC 7252. În mod implicit, serverul UDP așteaptă cereri la portul 5683.

Scopul protocolului CoAP este să ofere o interfață RESTful (similară HTTP) pentru dispozitive și rețele cu resurse limitate, utilizând mesaje scurte, cu latență redusă și opțiuni simple de confirmare. 

# Facilități implementate
- Transfer și stocare de fișiere
- Navigare prin directoare
- Comunicare confirmabilă (CON) sau neconfirmabilă (NON)

# Structura unui mesaj
Header-ul unui datagram COAP este simplu, începând cu un header fix de 4 octeți, urmat de Token-ul de lungime variată, și opțional separator (OxFF) și Payload.
```
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |Ver| T |  TKL  |      Code     |          Message ID           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |   Token (if any, TKL bytes) ...                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |1 1 1 1 1 1 1 1|    Payload (if any) ...                       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                         Formatul mesajelor
```
Observație: toate câmpurile sunt de tip unsigned integer

Octet 0:
- Version (VER) - 2 biți - indică versiunea COAP (01 binar) 
- Type (T) - 2 biți - indică tipul mesajului (CON, NON, ACK, RST)
- Token Length (TKL) - 4 biți - indică lungimea tokenului (0-8 octeți)

Octet 1:
- Code - 8 biți - Tip cerere/ cod răspuns

Octeți 2-3: 
- Message ID - 16 biți - Identificator unic de mesaj
  
Partea flexibilă:

- Token - 0-8 octeți - Identificator cerere
- Separator - 0xFF
- Payload - variabil - Conținut propriu zis

## Câmpul Type- tipuri de mesaje
- Cod 00 -> Tip CON -> Confirmabil, necesită Acknowledgement ACK
- Cod 01 -> Tip NON -> Neconfirmabil, fără ACK
- Cod 10 -> Tip ACK -> Confirmare pentru un CON
- Cod 11 -> Tip RST -> Reset - Eroare/Pachet invalid


Este implementată funcționalitatea de ack+ răspuns piggybacked pentru răspunsuri de dimensiuni mici.

Întâi este trimis un ACK cu empty message, apoi sunt expediate datele/fragmentele.

#### Comportament server:
- Primește CON -> Trimite **ACK** cu empty message și apoi răspuns/ ACK cu răspuns piggybacked
- Primește NON -> trimite răspuns direct
- Mesaj invalid -> trimite **RST**

```
                   +----------+-----+-----+-----+-----+
                   |          | CON | NON | ACK | RST |
                   +----------+-----+-----+-----+-----+
                   | Request  | X   | X   | -   | -   |
                   | Response | -   | X   | X   | -   |
                   | Empty    | -   | -   | X   | X   |
                   +----------+-----+-----+-----+-----+
                       Folosirea tipurilor de mesaje
```


## Câmpurile Token Length și Token
**Token Length** este un câmp pe 4 biți fără semn care indică lungimea câmpului Token (0–8 octeți). Valorile 9–15 sunt rezervate — nu trebuie trimise și, dacă sunt primite, trebuie tratate ca eroare de format al mesajului.

**Token-ul** este folosit pentru corelarea cererilor și răspunsurilor:
- Fiecare mesaj CoAP conține un token.
- Fiecare cerere conține un token generat de client.
- Serverul trebuie să echoeze tokenul exact (nemodificat) în răspunsul corespunzător.
- Clientul ar trebui să folosească un token aleator, non-trivial, pentru a se proteja împotriva răspunsurilor falsificate (spoofing).


## Câmpul Code -codul mesajului
Formatul codului: 'c.dd' , unde c- Clasa ( 0 = Request, 2 = Success, 4 = Client Error, 5 = Server Error ) 

Valoarea numerică = `(class << 5) | detail`

### Coduri de cerere

| Cod | Metodă | Descriere |
|------|---------|-----------|
| `0.01` | GET | Obține o resursă (listare/descărcare) |
| `0.02` | POST | Creează resursă (încărcare) |
| `0.03` | PUT | Actualizează resursă |
| `0.04` | DELETE | Șterge resursă |
| `0.05` | LS | Listează fișierele dintr-un director |

Un mesaj gol are câmpul Code setat la 0.00. Câmpul Token Length TREBUIE să fie setat la 0, iar niciun octet de date NU TREBUIE să fie prezent după câmpul Message ID. Dacă există octeți, aceștia TREBUIE să fie tratați ca o eroare de format a mesajului.

### Comanda personalizată LIST 

- Răspuns: 2.05 Content (cod 69)

- Exemplu de flux:

```
Client → Server: [CON][0.05 LIST]["docs/"]
Server → Client: [ACK][2.05 Content]["file1.txt\nfile2.txt"]
```

#### Structura pentru payload
- Cerere:
```
{
    "folder_path": "/path/to/folder",
    "file_type": "dir",
    "content": [
        {
            "file_name": "dir_name",
            "payload_size": "0",
            "fragment_count": "1:,
            "is_last_fragment": "1",
            "file_content": "" 
        }
    ]
}
```
- Răspuns (pentru simplificare, considerăm că nu va fi necesară fragmentarea pentru acest răspuns):
```
{
    "folder_path": "/path/to/folder",
    "file_type": "txt",
    "content": [
        {
            "file_name": "dir_name",
            "payload_size": "164",
            "fragment_count": "1:,
            "is_last_fragment": "1",
            "file_content": "codificarea(""file1.txt\nfile2.txt\nother_dir")
        }
    ]
}
```

#### Coduri de răspuns

| Cod | Semnificație | Utilizare |
|------|---------------|-----------|
| `2.00` | Empty Message| ACK/RST|
| `2.01` | Created | Răspuns la POST |
| `2.02` | Deleted | Răspuns la DELETE |
| `2.04` | Changed | Răspuns la PUT |
| `2.05` | Content | Răspuns la GET și LS |
| `4.00` | Bad Request | Cerere invalidă |
| `4.04` | Not Found | Resursă inexistentă |
| `5.00` | Internal Error | Eroare de procesare |

Răspuns: `2.05 (Content) = (2<<5)|5 = 0x45 (69)`

### Exemple efective pentru dinamica cerere-răspuns
1. GET fișier (descărcare)
```
Client → Server: [CON][0.01 GET]["/files/document.txt"]
Server → Client: [ACK][2.05 Content]["file_content": "…"]
```

2. POST fișier (upload)
```
Client → Server: [CON][0.02 POST]["/files/", content={"file_name":"doc.txt", "file_content":"…"}]
Server → Client: [ACK][2.00 Empty Message][]
Server → Client: [NON][2.01 Created]["/files/doc.txt"]
```
3. PUT fișier (actualizare)
```
Client → Server: [CON][0.03 PUT]["/files/doc.txt", content={"file_content":"…nou…"}]
Server → Client: [ACK][2.00 Empty Message][]
Server → Client: [NON][2.04 Changed]["/files/doc.txt"]
```
4. DELETE fișier
```
Client → Server: [CON][0.04 DELETE]["/files/doc.txt"]
Server → Client: [ACK][2.02 Deleted]["/files/doc.txt"]
```
5. LIST director (comandă personalizată LS)
```
Client → Server: [CON][0.05 LS]["/files/"]
Server → Client: [ACK][2.00 Empty Message][]
Server → Client: [NON][2.05 Content]["file_list":["doc1.txt","doc2.txt"]]
```
6. Non-confirmable (NON)
```
Client → Server: [NON][0.01 GET]["/status"]
Server → Client: [NON][2.05 Content]["status":"ok"]
```
7. Mesaj fragmentat
```
Client → Server: [CON][0.01 GET]["/content"]
Server → Client: [ACK][2.00 Empty Message][]
Server → Client: [NON][2.05 Content][json_with_payload_content] (fragment 1 cu Message_ID1)
Server → Client: [NON][2.05 Content][json_with_payload_content] (fragment 2 cu Message_ID1+1)
Server → Client: [NON][2.05 Content][json_with_payload_content] (fragment 3 cu Message_ID1+2)
...

```

## Câmpul Message ID

Scopul acestui câmp este detectarea mesajelor duplicate și asocierea mesajelor de tip Acknowledgement (ACK) sau Reset (RST) cu mesajele de tip Confirmable (CON) sau Non-confirmable (NON)

Precizăm faptul că ordinea de transmitere a octeților este Network byte order (big-endian).

Message ID este generat de expeditor atunci când trimite un mesaj Confirmable sau Non-confirmable și este inclus în header-ul CoAP. Message ID trebuie să fie reproduse exact (echo) în mesajele ACK sau RST de către server. Mai multe strategii de implementare pot fi folosite pentru generarea ID-urilor de Mesaj. În cel mai simplu caz, un endpoint CoAP generează ID-uri de Mesaj menținând o singură variabilă pentru ID-ul de Mesaj, care este schimbată de fiecare dată când este trimis un mesaj Confirmabil sau Neconfirmabil, indiferent de adresa sau portul destinației.

Același Message ID nu trebuie reutilizat (în comunicarea cu același endpoint) în intervalul EXCHANGE_LIFETIME. EXCHANGE_LIFETIME reprezintă durata maximă în care un Message ID rămâne activ pentru detectarea duplicatelor și asocierea răspunsurilor.

```
Octet 0 (MSB)  | Octet 1(LSB)
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Message ID         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

## Formatul pentru Options

Options sunt câmpuri opționale care transmit parametri suplimentari ai mesajului CoAP. Sunt codificate compact, pentru a minimiza traficul pe rețele cu resurse limitate.
Exemple de utilizare: specificarea resursei `(Uri-Path)`, tipul conținutului (`Content-Format`), time-to-live, etc.

Pentru simplificare, se vor implementa acestea in payload.

## Formatul pentru Payload

Payload-ul reprezintă conținutul efectiv al mesajului și este opțional. Este plasat după separatorul 0xFF. Lungimea și conținutul depind de metoda cererii.

Payload-ul va fi in format JSON ca in exemplul de mai jos:

```
{
    "folder_path": "/path/to/folder",
    "file_type": "txt",
    "content": [
        {
            "file_name": "document",
            "payload_size": "643",
            "fragment_count": "1:,
            "is_last_fragment": "0",
            "file_content": "codificarea=unui=document" 
        }
    ]
}
```
- In cazul creeri unui director, campul content va fi lasat gol iar "folder type" va fi "dir".
- Câmpul is_last_fragment este setat 1 atunci când fragmentul reprezintă ultimul mesaj dintr-un răspuns. Dacă nu este necesară fragmentarea, acesta este setat pe 1.
- În cazul cererilor, payload_size se lasă 0 și file_content va fi gol
- folder_path reprezintă calea până la **directorul din care face parte documentul/directorul** pentru care se efectuează cererea

# Confirmare și retransmisie

Pentru mesajele **confirmabile (CON)**:
Mesajele Confirmabile (CON) primite de server sunt procesate o singură dată, iar răspunsul este trimis imediat sub formă de ACK cu empty message/conținut piggybacked. Dacă clientul retransmite același mesaj din cauza pierderii ACK-ului, serverul retrimițe același payload fără a reprocesa cererea. 

- Dacă nu poate procesa cererea → trimite **RST**.
- Serverul trimite un **ACK** cu răspunsul după recepție.
- Dacă clientul nu primește ACK → repetă cererea -> retransmite cererea după un timeout.

În cazul mesajelor care necesită fragmentare, se răspunde în primă fază cu ACK cu empty message, urmând transmiterea răspunsului fragmentat sub formă de mesaje individuale. Fiecare fragement va avea un Message_ID individual, acestea fiind consecutive.

Pentru a marca ultimul fragment, se setează în payload câmpul "is_last_fragment" pe 1. Serverul va aștepta ACK de la client.

### La primirea unui mesaj CON

Se verifică dacă Message ID-ul există în cache:

- Da (duplicat) → retrimitem exact același răspuns cu payload, NU reprocesăm cererea
- Nu (primă apariție) → procesezăm cererea, generăm răspunsul, trimitem ACK gol + răspuns cu payload și adaugăm în cache.

### Structura mesajelor în cache:
 ```
recent_response = {
    "message_id": 101,
    "ack_response": my_msg,
    "expire_time": 123456
}
```
#### Exemplu de flux
```
Client trimite CON (Message ID 101)
Dacă cererea nu urmează un format corect/ nu poate fi procesată -> RST. Altfel:
Server verifică cache → nu există
    ↓
Server procesează cererea
Server trimite ACK gol
Server trimite răspuns
Server adaugă Message ID 101 în cache

Client nu primește ACK → retrimite CON 101
Server verifică cache → există!
    ↓
Server retrimite același răspuns

```

Curățare cache: Orice entry trebuie șters după ce expiră EXCHANGE_LIFETIME. Această funcționalitate este implementată și se efectuează automat.

#### Parametri pentru implementare- Timeout și retransmisii

CoAP implementează un mecanism de fiabilitate simplu pentru mesajele Confirmabile (CON), folosind retransmisii cu stop-and-wait și exponential back-off. Parametrii de bază pentru implementare sunt:

```
| Parametru               | Valoare recomandată (RFC 7252) | Descriere                                                                                                          |
| ----------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **ACK_TIMEOUT**         | 2 secunde                      | Timeout inițial înainte de prima retransmisie                                                                      |
| **ACK_RANDOM_FACTOR**   | 1.5                            | Factor de multiplicare random pentru a evita coliziunile (timeout efectiv = ACK_TIMEOUT × [1 … ACK_RANDOM_FACTOR]) |
| **MAX_RETRANSMIT**      | 4                              | Număr maxim de retransmisii pentru un mesaj Confirmabil                                                            |
| **RETRANSMIT_INTERVAL** | exponential                    | Intervalul între retransmisiile succesive se dublează: T, 2T, 4T, …                                                |
| **EXCHANGE_LIFETIME**   | 247 secunde                    | Durata maximă pentru care un schimb de mesaje (CON + ACK + eventual Răspuns) este considerat valid                 |

```

# Structura

Proiectarea acestui proiect va fi prezentată printr-o diagramă secvențială care este repezentată de 2 thread-uri

- main_thread: așteaptă sa primească cereri, deschide urmatorul thread
- receiver_tread: analizează cererea, trimite RST dacă messajul este invalid, verifică cache-ul daca conține deja cererea, altfel proceseaza cererea, pune in cache raspunsul, și îl trimite la client

  <img src="Sequence CoAP_2.png">
    
# Supliment: Arhitectura REST
Arhitectura REST (Representational State Transfer), propusă de Roy Thomas Fielding în teza sa de doctorat (2000), definește un stil arhitectural pentru sisteme distribuite bazate pe rețea, fundamentat pe principii de simplitate, scalabilitate și interoperabilitate.

REST descrie o interfață uniformă între componentele sistemului, în care resursele sunt identificate prin URI (Uniform Resource Identifiers) și manipulate prin reprezentări transferate între client și server (ex. JSON, XML, text, binar). Comunicarea este stateless – fiecare cerere HTTP (sau echivalent) conține toate informațiile necesare procesării, fără dependență de starea anterioară a conexiunii.

Modelul a stat la baza designului Web-ului modern și a fost adoptat ulterior în numeroase protocoale ușoare de comunicație — inclusiv CoAP, care transpune principiile REST peste UDP, pentru dispozitive cu resurse limitate.

### Pașii definitorii ai unui sistem RESTful
- Identificarea resurselor – fiecare entitate relevantă (fișier, utilizator, director etc.) primește un URI unic.
-- Exemplu: `/files/, /files/document.txt`
- Definirea metodelor de acces – operațiile asupra resurselor sunt efectuate prin metode uniforme (GET, POST, PUT, DELETE, PATCH, etc.).
- Stabilirea formatului de reprezentare – definirea modului de serializare a resurselor (ex: JSON, XML, text/plain, binar).
- Implementarea interfeței stateless – cererile conțin toate informațiile necesare (autentificare, parametri, payload).
- Gestionarea codurilor de răspuns – utilizarea codurilor standardizate (ex: 200 OK, 201 Created, 404 Not Found, 500 Internal Server Error).

# Supliment: Despre UDP
UDP (User Datagram Protocol) este un protocol de transport definit în RFC 768, care oferă un serviciu nesecurizat, fără conexiune (connectionless) și neorientat pe flux (message-oriented) peste IP. UDP nu oferă mecanisme interne de retransmisie, ordonare sau confirmare; toate acestea trebuie implementate la nivelul aplicației.

Este utilizat pentru aplicații care necesită viteză și eficiență mai mult decât fiabilitate (ex: DNS, VoIP, CoAP).

### Caracteristici principale
- Fără conexiune (connectionless) – nu există sesiuni sau handshake-uri între client și server.
- Fără garanția livrării – pachetele pot fi pierdute, duplicate sau sosite în altă ordine.
- Fără control de flux sau congestionare – responsabilitatea revine stratului superior (ex. aplicația CoAP).
- Low-overhead – header minim de 8 bytes.
- Transfer atomic de datagrame – fiecare apel sendto() / recvfrom() trimite sau primește un pachet complet.

### Construirea protocoalelor peste UDP
Deoarece UDP nu gestionează fiabilitatea, ordinea sau confirmările, protocoalele construite peste el (precum CoAP) trebuie să implementeze aceste mecanisme manual:
UDP oferă un canal simplu, nestructurat și rapid de transport, iar CoAP construiește peste el un strat logic de fiabilitate, identificare a mesajelor și confirmare, pentru a obține un comportament REST-like pe dispozitive cu resurse limitate.
  
| Funcționalitate | Implementare la nivel aplicație |
|------|---------------|
| Confirmare livrare | Mesaje ACK și retransmisii cu timeout |
| Detectarea duplicatelor | Identificatori unici de mesaj (ex: `Message ID` în CoAP) |
| Ordonarea mesajelor | Gestionată prin identificatori și logică de aplicație |
| Verificarea integrității | 	CRC sau checksum suplimentar la nivelul payloadului |

# Bibliografie

https://datatracker.ietf.org/doc/html/rfc7252

https://ics.uci.edu/~fielding/pubs/dissertation/fielding_dissertation.pdf

https://datatracker.ietf.org/doc/html/rfc768

https://lucid.app/

https://realpython.com/python-json/
