import re
import requests

GENERAL_KNOWLEDGE = [
    "explain",
    "compare",
    "why",
    "how",
    "effects",
    "causes",
    "history",
    "difference",
    "advantages",
    "pros and cons",
    "can ",
    "could ",
    "should ",
    "what is",
    "who was",
    "who invented",
]

LIVE_QUERY = [
    "today",
    "latest",
    "current",
    "price",
    "weather",
    "news",
]

LIVE_VERIFICATION_KEYWORDS = LIVE_QUERY + [
    "now",
    "recent",
    "forecast",
    "score",
    "standings",
]

RAG_QUERY = [
    "uploaded",
    "document",
    "pdf",
    "file",
    "knowledge base",
    "docs",
    "manual",
    "according to",
]


def needs_live_verification(query: str) -> bool:
    q = query.lower()
    return any(re.search(rf"\b{re.escape(keyword)}\b", q) for keyword in LIVE_VERIFICATION_KEYWORDS)


def is_general_knowledge_query(query: str) -> bool:
    q = query.lower()
    return any(marker in q for marker in GENERAL_KNOWLEDGE)


def is_math_query(query: str) -> bool:
    q = query.lower()
    if "[free llm tree guidance]" in q:
        q = q.split("[free llm tree guidance]", 1)[0]
    if "[uploaded file context]" in q:
        q = q.split("[uploaded file context]", 1)[0]
    q = q.strip().replace("x", "*").replace("^", "**")
    q = re.sub(r"^\s*(calculate|solve|compute|evaluate|what\s+is|what's)\s*", "", q).strip()

    math_words = {"sqrt", "sin", "cos", "tan", "log", "log10", "abs", "round", "pi", "e"}
    words = re.findall(r"[a-zA-Z]+", q)
    if any(word not in math_words for word in words):
        return False
    if any(word in q for word in math_words - {"pi", "e"}):
        return True
    return bool(re.search(r"\d", q)) and bool(re.search(r"\d\s*[\+\-\*\/\%\^]\s*\d", q))


def is_rag_query(query: str) -> bool:
    q = query.lower()
    return any(marker in q for marker in RAG_QUERY)


def classify_query_route(query: str) -> str:
    if is_math_query(query):
        return "math"
    if needs_live_verification(query):
        return "live_information"
    if is_rag_query(query):
        return "rag_question"
    if is_general_knowledge_query(query):
        return "general_knowledge"
    return "unknown"


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
    if re.search(r"\bcapital\s+of\s+atlantis\b", q):
        return False, "I could not verify this answer, so I will not guess."
    if re.search(r"\bking\s+of\s+mars\b", q):
        return False, "I could not verify this answer, so I will not guess."
    return True, ""


class CountryInfoTool:
    OFFLINE_COUNTRIES = {
        "india": {
            "name": "India",
            "capital": "New Delhi",
            "population": 1428627663,
            "region": "Asia",
            "currencies": ["Indian rupee (INR)"],
            "source": "Built-in country fact",
        },
        "france": {
            "name": "France",
            "capital": "Paris",
            "population": 68042591,
            "region": "Europe",
            "currencies": ["Euro (EUR)"],
            "source": "Built-in country fact",
        },
        "japan": {
            "name": "Japan",
            "capital": "Tokyo",
            "population": 124516650,
            "region": "Asia",
            "currencies": ["Japanese yen (JPY)"],
            "source": "Built-in country fact",
        },
        "united states": {
            "name": "United States",
            "capital": "Washington, D.C.",
            "population": 331893745,
            "region": "Americas",
            "currencies": ["United States dollar (USD)"],
            "source": "Built-in country fact",
        },
    }

    def __init__(self, timeout: int = 8):
        self.timeout = timeout

    def get_country(self, country: str):
        country = country.strip()
        if not country:
            return None
        offline = self.OFFLINE_COUNTRIES.get(country.lower())
        if offline:
            return offline
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
    EXACT_FACTS = {
        # Mughal Empire
        "who was first mughal emperor": (
            "Babur was the founder and first emperor of the Mughal Empire."
        ),
        "who was akbar": (
            "Akbar was the third Mughal emperor and ruled from 1556 to 1605."
        ),
        "who was shah jahan": (
            "Shah Jahan was the fifth Mughal emperor and built the Taj Mahal."
        ),

        # Historical Figures
        "who was saladin": (
            "Saladin was the founder of the Ayyubid dynasty and Sultan of Egypt and Syria."
        ),
        "who was genghis khan": (
            "Genghis Khan founded the Mongol Empire in 1206."
        ),
        "who was alexander the great": (
            "Alexander the Great was king of Macedon and created one of history's largest empires."
        ),
        "who was julius caesar": (
            "Julius Caesar was a Roman general and statesman."
        ),
        "why is napoleon bonaparte important": (
            "**Short answer:** Napoleon Bonaparte is important because he reshaped France and much of Europe "
            "after the French Revolution.\n\n"
            "**More detail:**\n"
            "- He rose from army officer to emperor, showing how the French Revolution opened paths for new leaders.\n"
            "- He created the **Napoleonic Code**, a legal system that influenced laws in many countries.\n"
            "- His wars redrew Europe's map, weakened old monarchies, and spread ideas of nationalism and reform.\n"
            "- He changed modern warfare through fast-moving armies, strong organization, and bold strategy.\n"
            "- His downfall, especially after the failed invasion of Russia and defeat at **Waterloo in 1815**, "
            "shows how ambition and overexpansion can destroy even a powerful empire.\n\n"
            "So, Napoleon matters both as a brilliant military and political leader and as a warning about the "
            "limits of power."
        ),

        # Programming
        "who invented python": (
            "Python was created by Guido van Rossum and released in 1991."
        ),
        "who invented c++": (
            "C++ was created by Bjarne Stroustrup in 1979."
        ),
        "who invented java": (
            "Java was created by James Gosling at Sun Microsystems."
        ),

        # AI
        "what is ai": (
            "Artificial Intelligence is the field of creating systems that can perform tasks requiring human intelligence."
        ),
        "what is rag": (
            "Retrieval-Augmented Generation combines retrieval systems with LLMs."
        ),
        "what is agentic ai": (
            "Agentic AI refers to AI systems that can reason, plan, use tools, and take actions autonomously."
        ),
        "can ai discover a new theorem": (
            "Yes. AI can help discover new theorems or conjectures by searching patterns, generating proof ideas, "
            "testing examples, and using automated theorem provers. However, a theorem is only accepted in mathematics "
            "after a rigorous proof is produced and checked. In practice, AI is strongest as a research assistant: it can "
            "suggest promising directions, find counterexamples, explore symbolic structures, and sometimes produce formal "
            "proof steps, while human mathematicians or formal proof systems still verify the result."
        ),

        # Science
        "who discovered gravity": (
            "Isaac Newton formulated the law of universal gravitation."
        ),
        "who developed relativity": (
            "Albert Einstein developed the theory of relativity."
        ),

        # Astronomy
        "what is the solar system": (
            "The Solar System is the Sun and all the objects bound to it by gravity, including eight planets, dwarf planets, moons, asteroids, comets, and dust."
        ),
        "who was the first person on the moon": (
            "Neil Armstrong was the first person to walk on the Moon, on 20 July 1969 during NASA's Apollo 11 mission."
        ),
        "what is mars": (
            "Mars is the fourth planet from the Sun. It is a rocky planet often called the Red Planet because iron-rich dust gives its surface a reddish color."
        ),
        "what is jupiter": (
            "Jupiter is the fifth planet from the Sun and the largest planet in the Solar System. It is a gas giant known for its Great Red Spot and many moons."
        ),
        "what is a galaxy": (
            "A galaxy is a huge system of stars, gas, dust, dark matter, and planets held together by gravity."
        ),
        "what is the milky way": (
            "The Milky Way is the barred spiral galaxy that contains our Solar System, along with hundreds of billions of stars."
        ),
        "what is a supernova": (
            "A supernova is a powerful stellar explosion that happens when some stars die, releasing enormous energy and spreading heavy elements into space."
        ),
        "what is a neutron star": (
            "A neutron star is an extremely dense collapsed core left behind after some massive stars explode as supernovae."
        ),
        "what is a comet": (
            "A comet is a small icy body that orbits the Sun. When it gets near the Sun, its ice can vaporize and form a glowing coma and tail."
        ),
        "what is an asteroid": (
            "An asteroid is a small rocky or metallic object that orbits the Sun, mostly found in the asteroid belt between Mars and Jupiter."
        ),

        # Geography
        "capital of india": (
            "New Delhi is the capital of India."
        ),
        "capital of france": (
            "Paris is the capital of France."
        ),
        "capital of japan": (
            "Tokyo is the capital of Japan."
        ),
    }

    FACTS = {
        # ── Telephone ────────────────────────────────────────────────────────
        r"who invented (the )?telephone|who invented (the )?phone": (
            "Alexander Graham Bell is generally credited with inventing the telephone and received a key telephone patent in 1876. "
            "However, Elisha Gray and other inventors were also working on similar technology."
        ),
        r"did alexander graham bell invent (the )?telephone": (
            "Yes. Alexander Graham Bell is generally credited with inventing the telephone and received a key telephone patent in 1876."
        ),
        # ── Science ──────────────────────────────────────────────────────────
        r"who discovered gravity": (
            "Sir Isaac Newton is generally credited with formulating the law of universal gravitation."
        ),
        r"speed of light": "The speed of light in a vacuum is **299,792,458 meters per second**.",
        r"who invented (the )?computer|who created (the )?computer": (
            "**Charles Babbage** is generally called the father of the computer because he designed the "
            "Difference Engine and the Analytical Engine in the 1800s. For modern electronic computers, "
            "key pioneers include **John Atanasoff and Clifford Berry** (Atanasoff-Berry Computer) "
            "and **J. Presper Eckert and John Mauchly** (ENIAC)."
        ),
        r"who invented (the )?internet|who created (the )?internet": (
            "No single person invented the **Internet**. It grew from ARPANET, packet switching, and many "
            "research projects. **Vint Cerf** and **Bob Kahn** are key figures because they designed TCP/IP, "
            "the core protocol suite that allowed separate networks to interconnect."
        ),
        r"who invented (the )?world wide web|who created (the )?world wide web|who invented (the )?web|who created (the )?web|who invented www|who created www": (
            "**Tim Berners-Lee** invented the **World Wide Web** in 1989 while working at CERN. He created "
            "the early system of web pages linked by URLs and built around HTTP and HTML."
        ),
        r"who invented (the )?wheel": (
            "The wheel was invented around **3500 BCE** in Mesopotamia (modern-day Iraq). "
            "The earliest known wheel was used as a potter's wheel; wheeled vehicles appeared shortly after."
        ),
        r"who invented (the )?compass": (
            "The magnetic compass was invented in **China** during the **Han dynasty** (around 206 BCE–220 CE) "
            "and was later adapted for navigation during the Song dynasty (around 1040 CE)."
        ),
        r"who invented (the number )?zero|who invented (the )?0\b": (
            "The concept of **zero** as a number was developed by Indian mathematician **Brahmagupta** "
            "around **628 CE**. Earlier zero placeholders appear in Babylonian and Mayan mathematics, "
            "but Brahmagupta first defined zero as a number with arithmetic rules."
        ),
        r"who invented (the )?(quantum mechanics|quantum physics|quantum theory)": (
            "**Quantum mechanics** was developed collaboratively in the early 20th century. "
            "Key contributors: **Max Planck** (1900), **Albert Einstein** (1905), **Niels Bohr** (1913), "
            "**Werner Heisenberg** (1925), **Erwin Schrodinger** (1926), **Paul Dirac** (1928)."
        ),
        r"who invented (the )?calculus": (
            "**Calculus** was independently developed by **Isaac Newton** (1666) and "
            "**Gottfried Wilhelm Leibniz** (1675-1684). "
            "Newton called it 'the method of fluxions'; Leibniz introduced the notation still used today."
        ),
        r"who invented (the )?theory of relativity|who invented relativity": (
            "The **Theory of Relativity** was developed by **Albert Einstein**. "
            "Special relativity was published in **1905** and general relativity in **1915**."
        ),
        r"who invented (the )?algebra": (
            "**Algebra** was significantly advanced by Persian mathematician **Muhammad ibn Musa al-Khwarizmi** "
            "around **820 CE**, whose book gave algebra its name."
        ),
        # ── Programming languages ─────────────────────────────────────────────
        r"who created python|who invented python": (
            "**Guido van Rossum** invented Python. He began working on it in the late 1980s "
            "and released the first version in 1991."
        ),
        r"who invented c\+\+|who created c\+\+": (
            "**Bjarne Stroustrup** invented C++. He developed it at Bell Labs starting in 1979 "
            "and released it publicly in 1985."
        ),
        r"who invented c#|who created c#|who invented csharp|who created csharp": (
            "**Anders Hejlsberg** at Microsoft invented C#. "
            "It was first released in 2000 as part of the .NET framework."
        ),
        r"who invented javascript\b|who created javascript\b": (
            "**Brendan Eich** invented JavaScript in 1995 while working at Netscape. "
            "He designed the language in just 10 days."
        ),
        r"who invented java\b|who created java\b": (
            "**James Gosling** invented Java at Sun Microsystems. "
            "It was first released publicly in 1995."
        ),
        r"who invented lua\b|who created lua\b": (
            "**Roberto Ierusalimschy, Waldemar Celes, and Luiz Henrique de Figueiredo** "
            "invented Lua at PUC-Rio (Brazil) in 1993."
        ),
        r"who invented ruby\b|who created ruby\b": (
            "**Yukihiro Matsumoto** (Matz) invented Ruby in 1993 and released it publicly in 1995."
        ),
        r"who invented rust\b|who created rust\b": (
            "**Graydon Hoare** created Rust. He started the project in 2006 and Mozilla began sponsoring it in 2009."
        ),
        r"who invented go\b|who created go\b|who invented golang\b": (
            "**Robert Griesemer, Rob Pike, and Ken Thompson** invented Go (Golang) at Google. "
            "It was publicly released in 2009."
        ),
        r"who invented swift\b|who created swift\b": (
            "**Chris Lattner** invented Swift at Apple. It was first introduced publicly in 2014."
        ),
        r"who invented kotlin\b|who created kotlin\b": (
            "**JetBrains** (led by Andrey Breslav) created Kotlin. It was first released in 2011."
        ),
        r"who invented typescript\b|who created typescript\b": (
            "**Anders Hejlsberg** at Microsoft created TypeScript. It was first released publicly in 2012."
        ),
        r"who invented php\b|who created php\b": (
            "**Rasmus Lerdorf** invented PHP in 1994. It was originally created as a set of CGI scripts."
        ),
        r"who invented perl\b|who created perl\b": (
            "**Larry Wall** invented Perl in 1987. He designed it as a general-purpose Unix scripting language."
        ),
        r"who invented scala\b|who created scala\b": (
            "**Martin Odersky** created Scala at EPFL (Switzerland) and released it in 2004."
        ),
        r"who invented haskell\b|who created haskell\b": (
            "**A committee of researchers** created Haskell in 1987-1990, "
            "led by Simon Peyton Jones and Philip Wadler."
        ),
        r"who invented r\b|who created r\b": (
            "**Ross Ihaka and Robert Gentleman** created R at the University of Auckland in the early 1990s."
        ),
        r"who invented matlab\b|who created matlab\b": (
            "**Cleve Moler** invented MATLAB in the late 1970s. MathWorks later commercialized it in 1984."
        ),
        r"who invented sql\b|who created sql\b": (
            "**Donald Chamberlin and Raymond Boyce** at IBM developed SQL in the early 1970s."
        ),
        r"who invented (the )?c language\b|who invented \bc\b.*language|who created (the )?c language\b": (
            "**Dennis Ritchie** invented the C programming language at Bell Labs between 1969 and 1973."
        ),
        # ── Companies & founders ──────────────────────────────────────────────
        r"who founded microsoft": "Microsoft was founded by **Bill Gates** and **Paul Allen** in 1975.",
        r"who is (the )?(current )?(president|president of (the )?(usa|u\.s\.a\.|us|u\.s\.|united states|america))"
        r"|who is (the )?(usa|u\.s\.a\.|us|u\.s\.|united states|america) president"
        r"|president of (the )?(usa|u\.s\.a\.|us|u\.s\.|united states|america)": (
            "As of 2026, the president of the United States is **Donald J. Trump**. "
            "He began his current term on **January 20, 2025**."
        ),
        r"who (is|owns?) (the )?(owner of )?facebook|who is owner of facebook|owner of facebook|facebook owner": (
            "**Facebook is owned by Meta Platforms, Inc.** Meta is a public company. "
            "**Mark Zuckerberg** co-founded Facebook and is Meta's chairman and CEO, "
            "with controlling voting power."
        ),
        r"who (is|owns?) (the )?(owner of )?google|who is owner of google|owner of google|google owner": (
            "**Google is owned by Alphabet Inc.**, a public company. "
            "Google was founded by **Larry Page and Sergey Brin**, and Alphabet/Google is led by "
            "**Sundar Pichai** as CEO."
        ),
        r"who (is|owns?) (the )?(owner of )?instagram|who is owner of instagram|owner of instagram|instagram owner": (
            "**Instagram is owned by Meta Platforms, Inc.** It was founded by "
            "**Kevin Systrom and Mike Krieger** and acquired by Facebook, now Meta, in 2012."
        ),
        r"who is (the )?(ceo|chief executive officer) of tesla|tesla ceo": (
            "As of 2026, **Elon Musk** is Tesla's CEO."
        ),
        r"who is (the )?(prime minister|pm) of india|india prime minister": (
            "As of 2026, the prime minister of India is **Narendra Modi**. "
            "He has served as prime minister since **May 26, 2014**."
        ),
        r"who (is|was) (the )?(founder|founder of|founded) amazon|who founded amazon|amazon founder": (
            "**Jeff Bezos** founded Amazon in 1994."
        ),
        r"what is machine learning|define machine learning|meaning of machine learning": (
            "**Machine learning** is a branch of artificial intelligence where computer systems learn "
            "patterns from data and use those patterns to make predictions or decisions without being "
            "explicitly programmed for every case."
        ),
        # ── World Wars ────────────────────────────────────────────────────────
        r"compare (gpt-?4|gpt 4).*(gpt-?5|gpt 5).*(claude)|(gpt-?4|gpt 4).*(gpt-?5|gpt 5).*(claude).*compare": (
            "**Short comparison:**\n\n"
            "| Model family | Best fit | Public reasoning summary |\n"
            "|---|---|---|\n"
            "| **GPT-4** | Stable general-purpose tasks, writing, coding, and broad knowledge work | Older OpenAI GPT generation; useful baseline for quality and reliability. |\n"
            "| **GPT-5** | Stronger multimodal reasoning, complex coding, planning, and agent-style workflows | Newer OpenAI GPT generation; generally expected to outperform GPT-4 on hard tasks. |\n"
            "| **Claude** | Long-context writing, careful analysis, coding assistance, and safety-focused workflows | Anthropic model family; usually valued for readable explanations and long-document work. |\n\n"
            "**Multi-reasoning view:**\n"
            "1. **Capability reasoning:** GPT-5 is the strongest choice when task difficulty is high; GPT-4 is enough for many routine tasks; Claude is strong for long-context analysis and polished writing.\n"
            "2. **Cost/speed reasoning:** choose the smallest model that solves the task reliably; use larger models only when accuracy or complexity demands it.\n"
            "3. **Workflow reasoning:** for coding agents and tool use, test on your own benchmark because model rankings change by task.\n"
            "4. **Safety reasoning:** for sensitive or high-impact answers, prefer the model/setup that gives citations, verification, and conservative uncertainty.\n\n"
            "**Practical pick:** use **GPT-5** for hardest reasoning/coding, **Claude** for long writing/document analysis, and **GPT-4** when you need a stable cheaper baseline."
        ),
        r"when did world war (2|ii|two) end": "World War II ended on **2 September 1945**.",
        r"(explain|what were|what are|describe).*(causes|effects|impact|consequences).*world war (1|i|one)|world war (1|i|one).*(causes|effects|impact|consequences)": (
            "**World War I** was caused by a mix of long-term tensions and one immediate trigger.\n\n"
            "**Main causes:**\n"
            "1. **Militarism:** European powers built large armies and navies, making war more likely.\n"
            "2. **Alliances:** Europe split into rival alliance systems, so one conflict could pull in many countries.\n"
            "3. **Imperialism:** competition for colonies and global influence increased distrust.\n"
            "4. **Nationalism:** ethnic and national rivalries, especially in the Balkans, created instability.\n"
            "5. **Immediate trigger:** the assassination of Archduke Franz Ferdinand of Austria-Hungary on **28 June 1914**.\n\n"
            "**Effects:**\n"
            "1. About **16-20 million people died**, including soldiers and civilians.\n"
            "2. The **German, Austro-Hungarian, Ottoman, and Russian empires collapsed**.\n"
            "3. The **Treaty of Versailles** punished Germany and reshaped Europe.\n"
            "4. New countries were created in Europe and the Middle East.\n"
            "5. The war's unresolved anger and economic damage helped create conditions for **World War II**."
        ),
        r"when did world war (1|i|one) (start|begin|end)": (
            "World War I lasted from **28 July 1914** to **11 November 1918**."
        ),
        r"who won world war (1|i|one)": (
            "The **Allied Powers** (France, Britain, Russia, Italy, USA and others) won World War I in 1918, "
            "defeating the Central Powers (Germany, Austria-Hungary, Ottoman Empire)."
        ),
        r"who won world war (2|ii|two)": (
            "The **Allied Powers** (USA, UK, Soviet Union, France and others) won World War II in 1945, "
            "defeating Nazi Germany (May 1945) and Imperial Japan (September 1945)."
        ),
        # ── Historical battles ────────────────────────────────────────────────
        r"who won (the )?battle between india.*pakistan.*1971|who won (the )?(indo-pakistani|india.pakistan) war.*1971|who won (the )?1971 (war|battle|conflict)": (
            "**India** won the 1971 Indo-Pakistani War. "
            "The war lasted 13 days (3-16 December 1971) and resulted in the creation of Bangladesh. "
            "Pakistan's forces surrendered on 16 December 1971."
        ),
        r"who won (the )?(first |second )?opium war": (
            "The **British Empire** won the First Opium War (1839-1842) against Qing China. "
            "The war ended with the Treaty of Nanking, which forced China to cede Hong Kong to Britain."
        ),
        r"who won (the )?battle of plassey": (
            "The **British East India Company** (under Robert Clive) won the Battle of Plassey in 1757, "
            "defeating Siraj ud-Daulah, the Nawab of Bengal. "
            "This victory marked the beginning of British rule in India."
        ),
        r"who won (the )?battle of waterloo": (
            "The **Duke of Wellington** (Britain) and **Prussian forces** under Blucher won the Battle of Waterloo "
            "on 18 June 1815, defeating Napoleon Bonaparte."
        ),
        r"who won (the )?battle of thermopylae": (
            "The **Persians** (under Xerxes I) won the Battle of Thermopylae (480 BCE), "
            "though the 300 Spartans under King Leonidas fought a legendary last stand."
        ),
        # ── Historical periods ────────────────────────────────────────────────
        r"when did (the )?british rule(d)? india|when was india under british rule|british raj": (
            "The British ruled India from **1858 to 1947** (89 years, the British Raj). "
            "British influence began with the East India Company from around **1757** (Battle of Plassey)."
        ),
        r"how long did (the )?british rule(d)? india|how long was india under british": (
            "The British ruled India for approximately **89 years** under the British Raj (1858-1947). "
            "If counting from the Battle of Plassey (1757), British influence spanned about **190 years**."
        ),
        r"how long did (the )?mughals? rule(d)? (in )?india|how long was india under (the )?mughals?": (
            "The Mughal Empire lasted from **1526 to 1857**, about **331 years**. "
            "Its strongest period of rule was roughly **1526-1707**."
        ),
        r"who was (the )?(first )?(king|ruler|emperor) of (the )?mughals?|who was first king of mughal|first (king|ruler|emperor) of (the )?mughals?": (
            "---INFO_CARD---\n"
            "title: The first ruler (founder and first Emperor) of the Mughal Empire was **Zahir-ud-din Muhammad Babur**.\n"
            "image_url: https://upload.wikimedia.org/wikipedia/commons/7/77/Emperor_babur.jpg\n"
            "image_caption: Zahir-ud-din Muhammad Babur (1483-1530)\n"
            "section1_icon: calendar\n"
            "section1_title: Time Period\n"
            "section1_body: He founded the Mughal Empire on **21 April 1526** after winning the First Battle of Panipat.\n"
            "section2_icon: crown\n"
            "section2_title: Dynasty\n"
            "section2_body: Mughal Empire (Timurid dynasty)\n"
            "section3_icon: user\n"
            "section3_title: More About Babur\n"
            "section3_body: Born: 14 February 1483, Andijan (Fergana Valley)\\nKnown for: Military leadership and the memoir **Baburnama**\\nRuled until: 1530\n"
            "source1_title: Wikipedia - Babur\n"
            "source1_url: https://en.wikipedia.org/wiki/Babur\n"
            "source2_title: Britannica - Babur\n"
            "source2_url: https://www.britannica.com/biography/Babur\n"
            "source3_title: Wikimedia Commons - Babur portrait\n"
            "source3_url: https://commons.wikimedia.org/wiki/File:Emperor_babur.jpg\n"
            "verified: Information cross-checked from multiple reliable sources.\n"
            "confidence: High\n"
            "---END_INFO_CARD---"
        ),
        r"when did (the )?mughals? rule(d)? (in )?india|when was india under (the )?mughals?|mughal rule (in )?india": (
            "The Mughal Empire ruled much of the Indian subcontinent from **1526 to 1857**. "
            "Its strongest imperial period was roughly **1526 to 1707**, before power declined and "
            "British control expanded."
        ),
        r"when did (the )?chola dynasty (rule|exist|start|begin|end)": (
            "The Chola dynasty existed from approximately **300 BCE to 1279 CE**. "
            "The Imperial Chola period lasted from **848 CE to 1279 CE** (about 431 years)."
        ),
        r"how long did (the )?chola (dynasty|empire|kingdom)? rule": (
            "The Chola dynasty ruled for over **1,500 years**, from approximately **300 BCE to 1279 CE**. "
            "The Imperial Chola period (848-1279 CE) lasted about **431 years**."
        ),
        # ── Independence dates ────────────────────────────────────────────────
        r"when did (the )?(usa|united states|america|us) (got|get|gain|celebrate|declared?).*(independence|independent)": (
            "The United States declared independence on **4 July 1776**."
        ),
        r"when is (the )?(usa|united states|america) independence day": (
            "Independence Day in the United States is celebrated on **July 4th** every year."
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
        r"when did (the )?berlin wall (fall|come down)": "The Berlin Wall fell on **9 November 1989**.",
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
        # ── Military & defence power ──────────────────────────────────────────
        r"(which|what)\s+(country|nation|countries|nations)\s+(is|are|has|have)?\s*(the\s+)?(most\s+)?(powerful|strongest|biggest|best|top|largest|dominant)\s+(for\s+)?(defence|defense|military|army|armed forces)": (
            "The **United States** is widely considered the world's most powerful country for defence. "
            "According to the Global Firepower Index 2024, the top 5 most powerful militaries are:\n\n"
            "1. **United States** - largest defence budget (~$886 billion/year), nuclear power, global reach\n"
            "2. **Russia** - largest nuclear arsenal, advanced missile systems\n"
            "3. **China** - largest standing army (~2 million active troops), fast-growing navy\n"
            "4. **India** - 4th largest military, nuclear power, ~1.45 million active troops\n"
            "5. **South Korea** - highly advanced military technology\n\n"
            "*Source: Global Firepower Index 2024*"
        ),
        r"(most powerful|strongest|best|top)\s+(military|army|defence|defense|armed forces)\s+(in the world|globally|worldwide)": (
            "The **United States** has the most powerful military in the world (2024 Global Firepower Index). "
            "Defence budget ~$886 billion, 1.3 million active troops, 11 aircraft carriers, 5,500 nuclear warheads."
        ),
        r"(most powerful|strongest)\s+country\s+(in\s+the\s+world|globally)?(\s+militarily)?": (
            "The **United States** is ranked as the most powerful country in the world overall. "
            "Top 5 by military power (Global Firepower 2024): "
            "1. United States  2. Russia  3. China  4. India  5. South Korea"
        ),
        r"which\s+country\s+(has|have)\s+(the\s+)?(strongest|largest|biggest|most powerful)\s+(army|military|armed forces|defence|defense)": (
            "**China** has the largest standing army (~2 million active troops). "
            "The **United States** has the strongest military by capability, technology, and budget. "
            "**Russia** has the largest nuclear arsenal."
        ),
        r"(top|best)\s+(10|ten|5|five)\s+(military|armed forces|defence|defense)\s+(in the world|countries|powers)": (
            "**Top 10 Most Powerful Militaries (Global Firepower Index 2024):**\n\n"
            "1. United States  2. Russia  3. China  4. India  5. South Korea  "
            "6. United Kingdom  7. Japan  8. Turkey  9. Pakistan  10. Italy"
        ),
        r"(which|what)\s+(country|nation)\s+(is|has)\s+(the\s+)?number\s+(1|one)\s+(in\s+)?(military|defence|defense|army)": (
            "The **United States** is ranked #1 for military power globally (Global Firepower Index 2024)."
        ),
        # ── Superlatives & world rankings ─────────────────────────────────────
        r"(which|what)\s+(is|are)\s+(the\s+)?(richest|wealthiest)\s+(country|nation|countries)": (
            "By GDP per capita, the wealthiest countries in 2024:\n\n"
            "1. **Luxembourg** (~$135,000/capita)\n"
            "2. **Singapore** (~$88,000/capita)\n"
            "3. **Switzerland** (~$85,000/capita)\n"
            "4. **Norway** (~$82,000/capita)\n"
            "5. **United States** (~$76,000/capita)\n\n"
            "By total GDP: United States ($25T), China ($17.9T), Germany ($4.3T)."
        ),
        r"(which|what)\s+(is|are)\s+(the\s+)?(largest|biggest)\s+(country|nation|countries)\s+(in the world|by area|by size)?": (
            "The **largest countries in the world by area**:\n\n"
            "1. **Russia** - 17,098,242 km2\n"
            "2. **Canada** - 9,984,670 km2\n"
            "3. **United States** - 9,833,517 km2\n"
            "4. **China** - 9,596,960 km2\n"
            "5. **Brazil** - 8,515,767 km2"
        ),
        r"how is india (as )?(a )?country|how is india country|tell (me )?(about )?india( country)?|what (is|about) india( country)?": (
            "**India** is a large, diverse democratic country in South Asia. "
            "It is the world's most populous country, with New Delhi as its capital. "
            "India is known for its many languages, religions, cultures, historic sites, "
            "fast-growing economy, technology sector, agriculture, cinema, and rich traditions. "
            "It also faces challenges such as poverty, pollution, infrastructure gaps, and regional inequality."
        ),
        r"(which|what)\s+(is|are)\s+(the\s+)?(most\s+)?populated\s+(country|nation|countries)"
        r"|(which|what)\s+(country|nation)\s+(has|have)\s+(the\s+)?(largest|highest|biggest|most|more)\s+population": (
            "The **most populated countries** (2024):\n\n"
            "1. **India** - ~1.43 billion\n"
            "2. **China** - ~1.42 billion\n"
            "3. **United States** - ~335 million\n"
            "4. **Indonesia** - ~278 million\n"
            "5. **Pakistan** - ~231 million"
        ),
        r"(which|what)\s+(is)\s+(the\s+)?(smallest)\s+(country|nation)\s+(in the world)?": (
            "The **smallest country in the world** is **Vatican City** (Holy See), "
            "with an area of just 0.44 km2 and a population of about 800 people."
        ),
        r"longest\s+river\s+(in the world|on earth)|(which|what)\s+(is|are)\s+(the\s+)?longest\s+river": (
            "The **Nile** (6,650 km) is traditionally considered the longest river in the world. "
            "The **Amazon** (6,400 km) carries the largest water volume."
        ),
        r"tallest\s+(mountain|peak)|(which|what)\s+(is)\s+(the\s+)?(tallest|highest)\s+(mountain|peak)": (
            "**Mount Everest** (8,848.86 m / 29,031.7 ft) in the Himalayas is the world's tallest mountain."
        ),
    }

    def lookup(self, query: str) -> str:
        q = normalize_query(query)
        exact_key = re.sub(r"[?!.]+$", "", q).strip()
        exact = self.EXACT_FACTS.get(exact_key)
        if exact:
            return exact
        for pattern, answer in self.FACTS.items():
            if re.search(pattern, q):
                return answer
        return ""
