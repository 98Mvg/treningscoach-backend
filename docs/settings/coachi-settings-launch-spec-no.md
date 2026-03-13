# Coachi Settings Launch Spec (NO)

## Formål
Dette dokumentet beskriver en launch-klar settingsstruktur for Coachi. Det er skrevet for produkt, design og implementasjon, og bruker launch-sikker copy som matcher den aktive appflaten.

## Prinsipper
- Settings skal være enkle å forstå.
- Gratisbrukere skal ikke føle at appen er amputert.
- Premium skal presenteres som mer verdi, ikke som blokkering.
- Juridiske sider skal være tilgjengelige og tydelige.
- Teknisk vedlikehold av lydpakker skal ikke dominere hovedinnstillingene.
- Abonnement, gjenopprett kjøp og administrer abonnement skal være tilgjengelig med ett trykk når Premium er aktiv.

## Anbefalt informasjonsarkitektur

### Konto
- Profil
- Innlogging og konto
- Abonnement

### Coaching
- Puls og sensorer
- Coaching
- Talk to Coach

### Lyd og stemmer
- Språk
- Lydpakke
- Stemmer

### Historikk og data
- Treningshistorikk
- Data og personvern
- Eksporter data
- Slett treningsdata

### Hjelp og support
- FAQ
- Kontakt support
- Rapporter et problem

### Juridisk
- Personvernerklæring
- Vilkår for bruk

### Om appen
- Om Coachi
- Appversjon

## Launch-kritiske sider
Disse bør være synlige før launch:
- Profil
- Innlogging og konto
- Logg ut
- Slett konto
- Abonnement
- Administrer abonnement
- Gjenopprett kjøp
- Puls og sensorer
- Coaching
- Språk
- Lydpakke
- Treningshistorikk
- FAQ
- Kontakt support
- Personvernerklæring
- Vilkår for bruk
- Om Coachi
- Appversjon

## Sider som kan komme senere
- Stemmer
- Eksporter data
- Slett treningsdata som egen side
- Rapporter et problem
- Talk to Coach som egen settingsflate

## Side-for-side spesifikasjon

### Konto

#### Profil
**Formål:** La brukeren oppdatere grunnopplysninger som brukes i appen.  
**Synlighet:** Launch  
**Backend:** Delvis  
**Tittel:** `Profil`  
**Intro:** `Oppdater de grunnleggende opplysningene dine i Coachi.`

**Rader**
- `Navn`
- `Fødselsdato`
- `Språk`
- `Nivå`

#### Innlogging og konto
**Formål:** Tydelig vise kontostatus og kontohandlinger.  
**Synlighet:** Launch  
**Backend:** Ja  
**Tittel:** `Innlogging og konto`  
**Intro:** `Se hvordan kontoen din er koblet til appen, og administrer kontohandlinger.`

**Rader**
- `Innloggingsstatus`
  - Hjelpetekst: `Se hvordan du er logget inn i Coachi.`
- `Logg ut`
  - Hjelpetekst: `Logg ut av Coachi på denne enheten.`
- `Slett konto`
  - Hjelpetekst: `Slett kontoen din og tilhørende data i tråd med våre rutiner.`

#### Abonnement
**Formål:** Presentere gratis vs Premium og kjøpsrelaterte handlinger.  
**Synlighet:** Launch når Premium er aktiv i appen  
**Backend:** Ja  
**Tittel:** `Abonnement`  
**Intro:** `Se hva som er inkludert i Coachi Premium, og administrer kjøp og abonnement.`

**Rader**
- `Coachi Premium`
  - Hjelpetekst: `Mer innsikt, mer historikk og mer personlig coaching.`
- `Administrer abonnement`
  - Hjelpetekst: `Åpne abonnementet ditt og se status i App Store.`
- `Gjenopprett kjøp`
  - Hjelpetekst: `Gjenopprett tidligere kjøp på denne kontoen.`

### Coaching

#### Puls og sensorer
**Formål:** Forklare hvilke signaler Coachi kan bruke under økten.  
**Synlighet:** Launch  
**Backend:** Delvis  
**Tittel:** `Puls og sensorer`  
**Intro:** `Se hvilke sensorer Coachi kan bruke under øktene dine.`

**Rader**
- `Apple Watch`
- `Bluetooth-sensor`
- `Tilgjengelige kilder`
- `Hvordan Coachi bruker puls`
  - Hjelpetekst: `Når puls er tilgjengelig, kan coachingen bli mer presis.`

#### Coaching
**Formål:** Forklare hvordan Coachi guider brukeren gjennom økter.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Coaching`  
**Intro:** `Slik guider Coachi deg gjennom øktene dine.`

**Rader**
- `Hvordan Coachi fungerer`
  - Hjelpetekst: `Forstå hvordan appen bruker øktstruktur, lyd og puls.`
- `Hvis puls mangler`
  - Hjelpetekst: `Coachi fortsetter med strukturert coaching selv uten puls.`

#### Talk to Coach
**Formål:** Forklare taleinteraksjon og Premium-verdi når funksjonen er tilgjengelig.  
**Synlighet:** Senere hvis funksjonen ikke er stabil nok  
**Backend:** Ja  
**Tittel:** `Talk to Coach`  
**Intro:** `Still korte spørsmål under eller etter økten når funksjonen er tilgjengelig.`

**Rader**
- `Hva er Talk to Coach?`
- `Tilgjengelighet`
- `Begrensninger`
- `Premium`
  - Hjelpetekst: `Mer bruk og flere funksjoner er en del av Premium når abonnement er aktivt.`

### Lyd og stemmer

#### Språk
**Formål:** Velge app- og lydspråk.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Språk`  
**Intro:** `Velg hvilket språk Coachi skal bruke i app og lydcoaching.`

#### Lydpakke
**Formål:** Forklare og administrere lokalt lydinnhold.  
**Synlighet:** Launch  
**Backend:** Delvis  
**Tittel:** `Lydpakke`  
**Intro:** `Coachi bruker lokale lydfiler for rask og stabil coaching.`

**Rader**
- `Status for lydpakke`
- `Oppdater lydinnhold`
- `Rydd lokale lydfiler`
  - Hjelpetekst: `Fjern utdaterte lydfiler fra enheten.`

#### Stemmer
**Formål:** Gi et ryddig sted for stemmevalg senere.  
**Synlighet:** Senere  
**Backend:** Delvis  
**Tittel:** `Stemmer`  
**Intro:** `Velg hvilken stemme du vil høre i Coachi.`

**Rader**
- `Aktiv stemme`
- `Tilgjengelige stemmer`
- `Flere stemmer kommer senere`

### Historikk og data

#### Treningshistorikk
**Formål:** Gi oversikt over tidligere økter.  
**Synlighet:** Launch  
**Backend:** Ja  
**Tittel:** `Treningshistorikk`  
**Intro:** `Se tidligere økter og utviklingen din over tid.`

#### Data og personvern
**Formål:** Samle datarelatert informasjon på ett sted.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Data og personvern`  
**Intro:** `Få oversikt over hvilke data Coachi bruker og hvorfor.`

**Rader**
- `Hva vi lagrer`
- `Hvordan data brukes`
- `Personvernerklæring`

#### Eksporter data
**Formål:** Mulighet for dataportabilitet senere.  
**Synlighet:** Senere  
**Backend:** Ja  
**Tittel:** `Eksporter data`  
**Intro:** `Be om en kopi av dataene dine.`

#### Slett treningsdata
**Formål:** Brukerkontroll over treningshistorikk senere.  
**Synlighet:** Senere  
**Backend:** Ja  
**Tittel:** `Slett treningsdata`  
**Intro:** `Administrer treningsdataene som er lagret i Coachi.`

### Hjelp og support

#### FAQ
**Formål:** Svare raskt på vanlige spørsmål.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `FAQ`  
**Intro:** `Svar på vanlige spørsmål om Coachi.`

#### Kontakt support
**Formål:** Gi en tydelig support-vei.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Kontakt support`  
**Intro:** `Ta kontakt hvis du trenger hjelp eller vil rapportere et problem.`

**Rader**
- `Send e-post til support`
- `Rapporter et problem`

### Juridisk

#### Personvernerklæring
**Formål:** Forklare databehandling.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Personvernerklæring`  
**Intro:** `Les hvordan Coachi behandler personopplysninger.`

#### Vilkår for bruk
**Formål:** Forklare regler og ansvar ved bruk.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Vilkår for bruk`  
**Intro:** `Les vilkårene som gjelder for bruk av Coachi.`

### Om appen

#### Om Coachi
**Formål:** Gi kort appinfo og kontaktpunkter.  
**Synlighet:** Launch  
**Backend:** Nei  
**Tittel:** `Om Coachi`  
**Intro:** `Informasjon om appen, kontaktpunkter og versjon.`

**Rader**
- `Appversjon`
- `Nettside`
- `Kontakt`

## Foreslåtte labels og mikrotekst

### Seksjoner
- `Konto`
- `Coaching`
- `Lyd og stemmer`
- `Historikk og data`
- `Hjelp og support`
- `Juridisk`
- `Om appen`

### Konto
- `Profil`
- `Innlogging og konto`
- `Abonnement`
- `Logg ut`
- `Slett konto`

### Coaching
- `Puls og sensorer`
- `Hvordan Coachi fungerer`
- `Hvis puls mangler`
- `Talk to Coach`

### Lyd og stemmer
- `Språk`
- `Lydpakke`
- `Status for lydpakke`
- `Oppdater lydinnhold`
- `Rydd lokale lydfiler`

### Historikk og data
- `Treningshistorikk`
- `Data og personvern`
- `Eksporter data`
- `Slett treningsdata`

### Hjelp og support
- `FAQ`
- `Kontakt support`
- `Rapporter et problem`

### Juridisk
- `Personvernerklæring`
- `Vilkår for bruk`

### Om appen
- `Om Coachi`
- `Appversjon`

## Avklaringer som fortsatt kan forbedres senere
- Hvis juridiske dokumenter skal publiseres utenfor appen, bør formell selskapsidentitet og eventuell postadresse bekreftes i den publiserte versjonen.
- Hvis betalte abonnement lanseres senere, oppdateres abonnementskapitlene med pris, periode og oppsigelsesdetaljer.
