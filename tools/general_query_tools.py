import re
import requests


def clean_original_query(query: str) -> str:
    original = query
    if "[Free LLM Tree Guidance]" in original:
        original = original.split("[Free LLM Tree Guidance]", 1)[0].strip()
    if "[Uploaded File Context]" in original:
        original = original.split("[Uploaded File Context]", 1)[0].strip()
    return original.strip()


def normalize_query(query: str) -> str:
    q = query.lower().strip()
    replacements = {
        "popualation": "population",
        "capitol": "capital",
        "invented the phone": "invented the telephone",
        "invent the phone": "invent the telephone",
    }
    for old, new in replacements.items():
        q = q.replace(old, new)
    return q


def classify_question(query: str) -> str:
    q = normalize_query(query)
    if re.search(r"\bcapital\s+of\b", q):
        return "capital"
    if re.search(r"\bpopulation\s+of\b", q):
        return "population"
    if re.search(r"\bgdp\s+of\b|\bgross domestic product\s+of\b", q):
        return "gdp"
    if re.search(r"\bcurrency\s+of\b", q):
        return "currency"
    if q.startswith(("who invented", "who discovered", "who created", "who founded")):
        return "person_fact"
    if q.startswith(("did ", "does ", "do ", "is ", "are ", "was ", "were ", "has ", "have ")):
        return "yes_no"
    if q.startswith("when "):
        return "date"
    return "general"


def extract_entity_after_of(query: str, keyword: str) -> str:
    q = normalize_query(query)
    m = re.search(rf"\b{keyword}\s+of\s+([a-zA-Z][a-zA-Z\s\-.]+)", q)
    if not m:
        return ""
    entity = re.sub(r"[?!.]+$", "", m.group(1)).strip()
    return re.sub(r"\s+", " ", entity)


def validate_query(query: str):
    q = normalize_query(query)
    if "capital of paris" in q:
        return False, (
            "Paris is a city and therefore does not have a capital.\n\n"
            "You may be asking: **What is the capital of France?**\n\n"
            "Answer: Paris is the capital of France."
        )
    return True, ""


class CountryInfoTool:
    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def get_country(self, country: str):
        country = country.strip()
        if not country:
            return None
        try:
            r = requests.get(f"https://restcountries.com/v3.1/name/{country}", timeout=self.timeout)
            if r.status_code != 200:
                return None
            data = r.json()
            selected = data[0]
            for item in data:
                common = item.get("name", {}).get("common", "").lower()
                official = item.get("name", {}).get("official", "").lower()
                if country.lower() in [common, official]:
                    selected = item
                    break
            currencies = selected.get("currencies", {})
            currency_names = [f"{v.get('name', k)} ({k})" for k, v in currencies.items()]
            return {
                "name": selected.get("name", {}).get("common", country.title()),
                "capital": (selected.get("capital") or ["Unknown"])[0],
                "population": selected.get("population"),
                "region": selected.get("region", ""),
                "currencies": currency_names,
                "source": "RestCountries API",
            }
        except Exception:
            return None


class BuiltInFacts:
    FACTS = {
        r"who invented (the )?telephone|who invented (the )?phone": (
            "Alexander Graham Bell is generally credited with inventing the telephone and received a key telephone patent in 1876. "
            "However, Elisha Gray and other inventors were also working on similar technology."
        ),
        r"did alexander graham bell invent (the )?telephone": (
            "Yes. Alexander Graham Bell is generally credited with inventing the telephone and received a key telephone patent in 1876."
        ),
        r"who discovered gravity": (
            "Sir Isaac Newton is generally credited with formulating the law of universal gravitation."
        ),
        r"who created python": "Python was created by Guido van Rossum and first released in 1991.",
        r"who invented python|who created python": "**Guido van Rossum** invented Python. He began working on it in the late 1980s and released the first version in 1991.",
        r"who invented c\+\+|who created c\+\+": "**Bjarne Stroustrup** invented C++. He developed it at Bell Labs starting in 1979 and released it publicly in 1985.",
        r"who invented c#|who created c#|who invented csharp|who created csharp": "**Anders Hejlsberg** at Microsoft invented C#. It was first released in 2000 as part of the .NET framework.",
        r"who invented javascript\b|who created javascript\b": "**Brendan Eich** invented JavaScript in 1995 while working at Netscape. He designed the language in just 10 days.",
        r"who invented java\b|who created java\b": "**James Gosling** invented Java at Sun Microsystems. It was first released publicly in 1995.",
        r"who invented lua\b|who created lua\b": "**Roberto Ierusalimschy, Waldemar Celes, and Luiz Henrique de Figueiredo** invented Lua at PUC-Rio (Brazil) in 1993.",
        r"who invented ruby\b|who created ruby\b": "**Yukihiro Matsumoto** (also known as Matz) invented Ruby in 1993 and released it publicly in 1995.",
        r"who invented rust\b|who created rust\b": "**Graydon Hoare** created Rust. He started the project in 2006 and Mozilla began sponsoring it in 2009.",
        r"who invented go\b|who created go\b|who invented golang\b": "**Robert Griesemer, Rob Pike, and Ken Thompson** invented Go (Golang) at Google. It was publicly released in 2009.",
        r"who invented swift\b|who created swift\b": "**Chris Lattner** invented Swift at Apple. It was first introduced publicly in 2014.",
        r"who invented kotlin\b|who created kotlin\b": "**JetBrains** (led by Andrey Breslav) created Kotlin. It was first released in 2011.",
        r"who invented typescript\b|who created typescript\b": "**Anders Hejlsberg** at Microsoft created TypeScript. It was first released publicly in 2012.",
        r"who invented php\b|who created php\b": "**Rasmus Lerdorf** invented PHP in 1994. It was originally created as a set of CGI scripts.",
        r"who invented perl\b|who created perl\b": "**Larry Wall** invented Perl in 1987. He designed it as a general-purpose Unix scripting language.",
        r"who invented scala\b|who created scala\b": "**Martin Odersky** created Scala. He designed it at EPFL (Switzerland) and released it in 2004.",
        r"who invented haskell\b|who created haskell\b": "**A committee of researchers** created Haskell in 1987–1990, led by figures including Simon Peyton Jones and Philip Wadler.",
        r"who invented r\b|who created r\b": "**Ross Ihaka and Robert Gentleman** created R at the University of Auckland in the early 1990s.",
        r"who invented matlab\b|who created matlab\b": "**Cleve Moler** invented MATLAB in the late 1970s. MathWorks later commercialized it in 1984.",
        r"who invented sql\b|who created sql\b": "**Donald Chamberlin and Raymond Boyce** at IBM developed SQL in the early 1970s.",
        r"who invented (the )?c language\b|who invented \bc\b.*language|who created (the )?c language\b": "**Dennis Ritchie** invented the C programming language at Bell Labs between 1969 and 1973.",
        r"who founded microsoft": "Microsoft was founded by Bill Gates and Paul Allen in 1975.",
        r"when did world war (2|ii|two) end": "World War II ended on **2 September 1945**.",
        r"when did world war (1|i|one) (start|begin|end)": "World War I lasted from **28 July 1914** to **11 November 1918**.",
        r"who won (the )?battle between india.*pakistan.*1971|"
        r"who won (the )?(indo-pakistani|india.pakistan) war.*1971|"
        r"who won (the )?1971 (war|battle|conflict)": (
            "**India** won the 1971 Indo-Pakistani War. "
            "The war lasted 13 days (3–16 December 1971) and resulted in the "
            "creation of Bangladesh (formerly East Pakistan). Pakistan's forces "
            "surrendered on 16 December 1971 — one of the largest military surrenders since World War II."
        ),
        r"who won (the )?(first |second )?opium war": (
            "The **British Empire** won the First Opium War (1839–1842) against Qing China. "
            "The war ended with the Treaty of Nanking, which forced China to cede Hong Kong to Britain "
            "and open five treaty ports to British trade."
        ),
        r"who won (the )?battle of plassey": (
            "The **British East India Company** (under Robert Clive) won the Battle of Plassey in 1757, "
            "defeating Siraj ud-Daulah, the Nawab of Bengal. This victory marked the beginning of British rule in India."
        ),
        r"who won (the )?battle of waterloo": (
            "The **Duke of Wellington** (Britain) and **Prussian forces** under Blücher won the Battle of Waterloo "
            "on 18 June 1815, defeating Napoleon Bonaparte. This ended Napoleon's rule."
        ),
        r"who won (the )?battle of thermopylae": (
            "The **Persians** (under Xerxes I) won the Battle of Thermopylae (480 BCE), "
            "though the 300 Spartans under King Leonidas fought a legendary last stand."
        ),
        r"who won world war (1|i|one)": (
            "The **Allied Powers** (France, Britain, Russia, Italy, USA and others) won World War I in 1918, "
            "defeating the Central Powers (Germany, Austria-Hungary, Ottoman Empire)."
        ),
        r"who won world war (2|ii|two)": (
            "The **Allied Powers** (USA, UK, Soviet Union, France and others) won World War II in 1945, "
            "defeating Nazi Germany (May 1945) and Imperial Japan (September 1945)."
        ),
        r"when did (the )?british rule(d)? india|when was india under british rule|british raj": (
            "The British ruled India from **1858 to 1947** — a period of **89 years** known as the British Raj. "
            "British influence began earlier with the East India Company from around **1757** (Battle of Plassey), "
            "but formal Crown rule started in 1858 and ended with Indian independence on **15 August 1947**."
        ),
        r"how long did (the )?british rule(d)? india|how long was india under british": (
            "The British ruled India for approximately **89 years** under the British Raj (1858–1947). "
            "If counting from the Battle of Plassey (1757), British influence spanned about **190 years**."
        ),
        r"when did (the )?chola dynasty (rule|exist|start|begin|end)": (
            "The Chola dynasty existed from approximately **300 BCE to 1279 CE**. "
            "The Imperial Chola period (the most powerful phase) lasted from **848 CE to 1279 CE** — about 431 years."
        ),
        r"how long did (the )?chola (dynasty|empire|kingdom)? rule": (
            "The Chola dynasty ruled for over **1,500 years**, from approximately **300 BCE to 1279 CE**. "
            "The Imperial Chola period (848–1279 CE) lasted about **431 years**."
        ),
        r"speed of light": "The speed of light in a vacuum is **299,792,458 meters per second**.",
        # ── Inventor facts ────────────────────────────────────────────────
        r"who invented (the number )?zero|who invented (the )?0\b": (
            "The concept of **zero** as a number was developed by Indian mathematician **Brahmagupta** "
            "around **628 CE** in his work *Brahmasphutasiddhanta*. "
            "Earlier uses of a zero placeholder appear in Babylonian and Mayan mathematics, "
            "but Brahmagupta was the first to define zero as a number and establish rules for its use."
        ),
        r"who invented (the )?wheel": (
            "The wheel was invented around **3500 BCE** in Mesopotamia (modern-day Iraq). "
            "The earliest known wheel was used as a potter's wheel; wheeled vehicles appeared shortly after."
        ),
        r"who invented (the )?compass": (
            "The magnetic compass was invented in **China** during the **Han dynasty** (around 206 BCE–220 CE) "
            "and was later adapted for navigation during the Song dynasty (around 1040 CE)."
        ),
        r"who invented (the )?(quantum mechanics|quantum physics|quantum theory)": (
            "**Quantum mechanics** was not invented by a single person — it was developed collaboratively "
            "in the early 20th century. Key contributors include:\n"
            "- **Max Planck** (1900) — introduced the quantum of energy (Planck's constant)\n"
            "- **Albert Einstein** (1905) — explained the photoelectric effect using quanta\n"
            "- **Niels Bohr** (1913) — proposed the quantum model of the atom\n"
            "- **Werner Heisenberg** (1925) — formulated matrix mechanics and the uncertainty principle\n"
            "- **Erwin Schrödinger** (1926) — developed wave mechanics (Schrödinger equation)\n"
            "- **Paul Dirac** (1928) — unified quantum mechanics with special relativity"
        ),
        r"who invented (the )?calculus": (
            "**Calculus** was independently developed by **Isaac Newton** (1666) and "
            "**Gottfried Wilhelm Leibniz** (1675–1684). "
            "Newton called it 'the method of fluxions'; Leibniz introduced the notation still used today."
        ),
        r"who invented (the )?theory of relativity|who invented relativity": (
            "The **Theory of Relativity** was developed by **Albert Einstein**. "
            "Special relativity was published in **1905** and general relativity in **1915**."
        ),
        r"who invented (the )?algebra": (
            "**Algebra** was significantly advanced by Persian mathematician **Muhammad ibn Musa al-Khwarizmi** "
            "around **820 CE**, whose book *Al-Kitab al-mukhtasar fi hisab al-jabr wal-muqabala* "
            "gave algebra its name."
        ),
        # ── Independence dates ────────────────────────────────────────────
        r"when did (the )?(usa|united states|america|us) (got|get|gain|celebrate|declared?).*(independence|independent)": (
            "The United States declared independence on **4 July 1776**. "
            "The Declaration of Independence was adopted by the Continental Congress on that date, "
            "marking the birth of the United States as a nation."
        ),
        r"when is (the )?(usa|united states|america) independence day": (
            "Independence Day in the United States is celebrated on **July 4th** every year, "
            "commemorating the Declaration of Independence signed on **4 July 1776**."
        ),
        r"when did india (got|get|gain|become).*(independence|independent)": (
            "India gained independence from British rule on **15 August 1947**."
        ),
        r"when did pakistan (got|get|gain|become).*(independence|independent)": (
            "Pakistan gained independence from British India on **14 August 1947**."
        ),
        r"when did (the )?french revolution (start|begin|happen)": (
            "The French Revolution began in **1789** (storming of the Bastille on 14 July 1789) "
            "and lasted until **1799**."
        ),
        r"when did (the )?berlin wall (fall|come down)": (
            "The Berlin Wall fell on **9 November 1989**."
        ),
        r"when did (the )?soviet union (collapse|end|dissolve|break up)": (
            "The Soviet Union officially dissolved on **25 December 1991**."
        ),
        r"when did (the )?(titanic|rms titanic) (sink|sank)": (
            "The RMS Titanic sank on **15 April 1912** after hitting an iceberg in the North Atlantic."
        ),
        r"when did (the )?moon landing (happen|take place)|when did (humans?|man|nasa|apollo).*(land|walk).*(moon)": (
            "The first Moon landing happened on **20 July 1969** when Apollo 11 astronauts "
            "Neil Armstrong and Buzz Aldrin walked on the Moon."
        ),
    }

    def lookup(self, query: str) -> str:
        q = normalize_query(query)
        for pattern, answer in self.FACTS.items():
            if re.search(pattern, q):
                return answer
        return ""
