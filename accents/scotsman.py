from _shared import DISCORD_MESSAGE_END

from pink_accents import Accent


# https://github.com/unitystation/unitystation/blob/develop/UnityProject/Assets/ScriptableObjects/Speech/Scotsman.asset
class Scotsman(Accent):
    """Makes you less polite"""

    # this is insanity. maybe use prefix tree?
    WORDS = {
        r"about": "aboot",
        r"above": "`boon",
        r"accounts": "accoonts",
        r"across": "o`er",
        r"after": "efter",
        r"agree": "gree",
        r"all": "aw",
        r"almost": "a`maist",
        r"along": "alang",
        r"already": "awready",
        r"also": "an` a`",
        r"although": "althoogh",
        r"and": "`n`",
        r"another": "anither",
        r"any": "ony",
        r"anyone": "a`body",
        r"anybody": "a`body",
        r"anything": "anythin`",
        r"arrested": "liftit",
        r"arrest": "lift",
        r"arrests": "lifts",
        r"argues": "argies",
        r"argued": "argied",
        r"argue": "argie",
        r"around": "aroond",
        r"available": "free",
        r"avoiding": "jookin",
        r"avoided": "jooked",
        r"avoid": "jook",
        r"ask": "spir",
        r"assistant": "servand",
        r"assistants": "servands",
        r"asking": "spirin",
        r"asked": "spire'd",
        r"away": "awa`",
        r"babies": "bairns",
        r"baby": "bairn",
        r"bad": "ill",
        r"balls": "baws",
        r"ball": "baw",
        r"bars": "boozers",
        r"bar": "boozer",
        r"been": "buin",
        r"beautiful": "bonny",
        r"because": "fur",
        r"breakdown": "breakdoon",
        r"nap": "kip",
        r"napping": "kipin'",
        r"before": "afore",
        r"believes": "hawps",
        r"believing": "hawpin",
        r"believe": "hawp",
        r"between": "atween",
        r"boards": "boords",
        r"board": "boord",
        r"both": "baith",
        r"boxes": "kists",
        r"box": "kist",
        r"boy": "laddie",
        r"brother": "brither",
        r"brothers": "brithers",
        r"but": "bit",
        r"bitch": "cunt",
        r"captain": "caiptain",
        r"cap": "caip",
        r"calling": "ca`ing",
        r"called": "cawed",
        r"call": "caw",
        r"cars": "motors",
        r"car": "motor",
        r"cared": "car'd",
        r"cards": "cairds",
        r"card": "caird",
        r"careers": "joabs",
        r"career": "joab",
        r"cargo": "cargae",
        r"century": "hunner years",
        r"changed": "chaynged",
        r"change": "chaynge",
        r"chaplain": "priestheid",
        r"chief": "heid",
        r"child": "wee'un",
        r"childeren": "wee'uns",
        r"choosing": "walin",
        r"choose": "wale",
        r"churches": "kirks",
        r"church": "kirk",
        r"city": "toon",
        r"cities": "toons",
        r"closer": "claiser",
        r"closest": "claisest",
        r"close": "claise",
        r"clowns": "clouns",
        r"clown": "cloun",
        r"coats": "coaties",
        r"coat": "coatie",
        r"coldest": "cauldest",
        r"colder": "caulder",
        r"cold": "cauld",
        r"cooks": "keuks",
        r"cook": "keuk",
        r"consumer": "punter",
        r"consumers": "punters",
        r"could": "cuid",
        r"countries": "lands",
        r"country": "land",
        r"course": "coorse",
        r"courses": "coorses",
        r"cultures": "culchurs",
        r"culture": "culchur",
        r"customer": "punter",
        r"customers": "punters",
        r"daddy": "daddie",
        r"dark": "mirk",
        r"dad": "da",
        r"dead": "deid",
        r"deaf": "deav",
        r"deafen": "deave",
        r"deafened": "deaved",
        r"debate": "argie",
        r"debating": "argiein",
        r"debates": "argies",
        r"degrees": "grees",
        r"degree": "gree",
        r"detectives": "snoots",
        r"detective": "snoot",
        r"difficult": "pernicketie",
        r"dinner": "tea",
        r"directors": "guiders",
        r"director": "guider",
        r"did": "daed",
        r"do": "dae",
        r"dogs": "dugs",
        r"dog": "dug",
        r"down": "doon",
        r"downricht": "doun",
        r"droped": "draped",
        r"drops": "draps",
        r"drop": "drap",
        r"drink": "drappie",
        r"drinking": "swillin'",
        r"drank": "swilled",
        r"drunk": "fou",
        r"during": "while",
        r"dying": "deein'",
        r"each": "ilk",
        r"early": "earlie",
        r"eating": "slochin",
        r"ate": "sloched",
        r"eat": "sloch",
        r"edges": "lips",
        r"edge": "lip",
        r"enjoys": "gilravages",
        r"enjoy": "gilravage",
        r"engineer": "navvy",
        r"engineering": "ingineerin",
        r"engineers": "Navvies",
        r"evenings": "forenichts",
        r"evening": "forenicht",
        r"every": "ilka",
        r"everybody": "a`body",
        r"everyone": "a`body",
        r"eye": "ee",
        r"eyes": "e'ens",
        r"face": "physog",
        r"famililies": "fowks",
        r"family": "fowk",
        r"fast": "fleet",
        r"fathers": "faithers",
        r"father": "faither",
        r"fight": "rammy",
        r"fighting": "ramming",
        r"fights": "rammies",
        r"films": "pictures",
        r"film": "picture",
        r"finding": "fin`ing",
        r"found": "fund",
        r"fine": "braw",
        r"floors": "flairs",
        r"floor": "flair",
        r"foods": "fairns",
        r"food": "fairn",
        r"for": "fer",
        r"forget": "forgoat",
        r"friends": "mukkers",
        r"friend": "pal",
        r"from": "fae",
        r"full": "stowed oot",
        r"games": "gams",
        r"game": "gam",
        r"gardens": "back greens",
        r"garden": "back green",
        r"get": "git",
        r"girl": "lassie",
        r"give": "gie",
        r"glasses": "glesses",
        r"glass": "gless",
        r"go": "gae",
        r"good": "guid",
        r"great": "stoatin",
        r"growing": "grawing",
        r"grown": "grawn",
        r"grow": "graw",
        r"glared": "glower'd",
        r"glaring": "glowrin'",
        r"guess": "jalouse",
        r"had": "haed",
        r"has": "haes",
        r"hadnt": "haedna",
        r"hadn't": "haedna",
        r"hairs": "locks",
        r"hair": "locks",
        r"halfs": "haufs",
        r"half": "hauf",
        r"hands": "hauns",
        r"hand": "haun",
        r"hangs": "hings",
        r"hanging": "hinging",
        r"hang": "hing",
        r"have": "hae",
        r"heads": "heids",
        r"head": "heid",
        r"hearts": "herts",
        r"heart": "hert",
        r"help": "hulp",
        r"here": "`ere",
        r"high": "heich",
        r"himself": "his-sel",
        r"holding": "hauding",
        r"hold": "haud",
        r"homes": "hames",
        r"home": "hame",
        r"hopes": "hawps",
        r"hope": "hawp",
        r"hoter": "heter",
        r"hotest": "hetest",
        r"hot": "het",
        r"hotels": "change-hooses",
        r"hotel": "change-hoose",
        r"hours": "oors",
        r"hour": "oor",
        r"house": "hoose",
        r"houses": "hooses",
        r"how": "hou",
        r"husband": "guidman",
        r"images": "photies",
        r"image": "photie",
        r"imagine": "jalouse",
        r"including": "anaw",
        r"indicates": "shows",
        r"indicate": "show",
        r"informations": "speirins",
        r"information": "speirins",
        r"into": "intae",
        r"its": "tis",
        r"isn't": "isna",
        r"isnt": "isna",
        r"janitors": "jannies",
        r"janitor": "jannie",
        r"jobs": "jabs",
        r"joined": "jyneed",
        r"joins": "jynes",
        r"join": "jyne",
        r"just": "juist",
        r"kids": "bairns",
        r"kid": "bairn",
        r"kills": "murdurrs",
        r"killer": "murdurrur",
        r"killed": "murdurred",
        r"kill": "murdurr",
        r"kitchens": "sculleries",
        r"kitchen": "scullery",
        r"knows": "kens",
        r"know": "ken",
        r"known": "kent",
        r"languages": "leids",
        r"language": "leid",
        r"larger": "lairger",
        r"largest": "lairgest",
        r"large": "lairge",
        r"last": "lest",
        r"later": "efter",
        r"laughing": "roarin",
        r"laugh": "roar",
        r"lawyers": "advocates",
        r"lawyer": "advocate",
        r"lead": "leid",
        r"leading": "leidin",
        r"leaving": "leaing",
        r"leave": "lea",
        r"let": "loot",
        r"legs": "shanks",
        r"leg": "shank",
        r"devil": "deuce",
        r"devils": "deuces",
        r"lying": "liein",
        r"like": "lik`",
        r"likely": "likelie",
        r"little": "wee",
        r"longer": "langer",
        r"longest": "langest",
        r"long": "lang",
        r"looking": "keeking",
        r"looked": "keeked",
        r"look": "keek",
        r"loved": "loued",
        r"loving": "louing",
        r"love": "loue",
        r"makes": "mak`s",
        r"make": "mak`",
        r"men": "jimmies",
        r"manage": "guide",
        r"managers": "high heid yins",
        r"manager": "high heid yin",
        r"many": "mony",
        r"may": "mey",
        r"markets": "merkats",
        r"market": "merkat",
        r"marriages": "mairriages",
        r"marriage": "mairriage",
        r"matters": "maiters",
        r"matter": "maiter",
        r"maybe": "mibbie",
        r"meetings": "meetins",
        r"meeting": "meetin",
        r"methods": "ways",
        r"method": "way",
        r"might": "micht",
        r"mind": "mynd",
        r"miner": "pickman",
        r"miners": "pickmen",
        r"money": "dosh",
        r"months": "munths",
        r"month": "munth",
        r"more": "mair",
        r"mornings": "mornin`s",
        r"morning": "mornin`",
        r"most": "maist",
        r"mothers": "mithers",
        r"mother": "mither",
        r"mouths": "geggies",
        r"mouth": "geggy",
        r"moves": "shifts",
        r"move": "shift",
        r"much": "muckle",
        r"must": "mist",
        r"my": "ma",
        r"myself": "masell",
        r"nasty": "mingin",
        r"networks": "netwurks",
        r"network": "netwurk",
        r"never": "ne`er",
        r"new": "freish",
        r"news": "speirins",
        r"next": "neist",
        r"nice": "crakin`",
        r"nights": "nichts",
        r"night": "nicht",
        r"False": ("na", "aff"),
        r"not": "nae",
        r"nothing": "neithin'",
        r"now": "noo",
        r"numbers": "nummers",
        r"number": "nummer",
        r"of": "o`",
        r"offices": "affices",
        r"office": "affice",
        r"officers": "boabies",
        r"officer": "boaby",
        r"often": "aften",
        r"oh": "och",
        r"ok": "a`richt",
        r"old": "auld",
        r"oil": "ile",
        r"once": "wance",
        r"one": "wan",
        r"only": "ainlie",
        r"other": "ither",
        r"others": "ithers",
        r"ours": "oors",
        r"our": "oor",
        r"out": "oot",
        r"outside": "ootdoors",
        r"over": "ower",
        r"owns": "ains",
        r"own": "ain",
        r"owners": "gaffers",
        r"owner": "gaffer",
        r"paintings": "pentins",
        r"painting": "pentin",
        r"parts": "pairts",
        r"part": "pairt",
        r"partners": "bidies",
        r"partner": "bidie",
        r"party": "pairtie",
        r"pass": "bygae",
        r"past": "bygane",
        r"peoples": "fowks",
        r"people": "fowk",
        r"perhaps": "mibbie",
        r"person": "body",
        r"phones": "phanes",
        r"phone": "phane",
        r"places": "steids",
        r"place": "steid",
        r"plays": "speils",
        r"play": "speil",
        r"police": "polis",
        r"poor": "brassic",
        r"popular": "weel-kent",
        r"problems": "kinches",
        r"problem": "kinch",
        r"professionals": "perfaissionals",
        r"professional": "perfaissional",
        r"programs": "progrums",
        r"program": "progrum",
        r"provides": "gies",
        r"provide": "gie",
        r"prison": "preeson",
        r"Imprisonment": "impreesonment",
        r"prisoner": "preesoner",
        r"put": "pat",
        r"questions": "quaistions",
        r"question": "quaistion",
        r"quite": "ferr",
        r"radios": "trannies",
        r"radio": "tranny",
        r"rather": "ower",
        r"ready": "duin",
        r"really": "pure",
        r"red": "rid",
        r"relationships": "kinships",
        r"relationship": "kinship",
        r"remember": "mind",
        r"remembered": "minded",
        r"rights": "richts",
        r"right": "richt",
        r"roles": "parts",
        r"role": "part",
        r"round": "ruund",
        r"same": "identical",
        r"schools": "schuils",
        r"school": "schuil",
        r"scores": "hampden roars",
        r"score": "hampden roar",
        r"scuffed": "scotched",
        r"seasons": "seezins",
        r"season": "seezin",
        r"security": "polis",
        r"seconds": "seiconts",
        r"second": "seicont",
        r"several": "loads",
        r"shaked": "shoogled",
        r"shakes": "shoogles",
        r"shake": "shoogle",
        r"should": "shuid",
        r"shows": "shaws",
        r"showed": "shawed",
        r"show": "shaw",
        r"since": "sin",
        r"small": "wee",
        r"spoke": "spak",
        r"so": "sae",
        r"soldiers": "fighters",
        r"soldier": "fighter",
        r"sometimes": "whiles",
        r"somewhat": "somewhit",
        r"south": "sooth",
        r"sore": "sair",
        r"stands": "stauns",
        r"stand": "staun",
        r"stars": "starns",
        r"star": "starn",
        r"starts": "stairts",
        r"start": "stairt",
        r"stays": "bides",
        r"stay": "bade",
        r"stops": "stoaps",
        r"stop": "stoap",
        r"stores": "hains",
        r"store": "hain",
        r"struck": "strak",
        r"streets": "wynds",
        r"street": "wynd",
        r"strong": "pure tough",
        r"styles": "pure classes",
        r"style": "pure class",
        r"such": "sic",
        r"table": "buird",
        r"tables": "buirds",
        r"takes": "tak`s",
        r"take": "tak`",
        r"talks": "blethers",
        r"talk": "blether",
        r"tasks": "hings",
        r"task": "hing",
        r"teams": "gangs",
        r"team": "gang",
        r"televisions": "tellyboxes",
        r"television": "tellybox",
        r"terminal": "terminus",
        r"the": "th`",
        r"their": "thair",
        r"them": "thaim",
        r"there": "thare",
        r"these": "thae",
        r"they": "thay",
        r"things": "hings",
        r"thing": "hing",
        r"those": "they",
        r"through": "thro`",
        r"throughout": "throo`oot",
        r"throw": "chuck",
        r"threw": "chucked",
        r"to": "tae",
        r"today": "th`day",
        r"together": "th`gither",
        r"tonight": "th`nicht",
        r"too": "tae",
        r"told": "telt",
        r"tops": "taps",
        r"top": "tap",
        r"total": "tot",
        r"towns": "touns",
        r"town": "toun",
        r"tough": "hard",
        r"traitors": "quislings",
        r"traitor": ("quisling", "traitor"),
        r"troubles": "trauchles",
        r"trouble": "trauchle",
        r"turds": "jobbies",
        r"turd": "jobbie",
        r"turn": "caw",
        r"TVs": "tellies",
        r"TV": "telly",
        r"two": "twa",
        r"understand": "ken",
        r"until": "`til",
        r"uses": "uises",
        r"use": "uise",
        r"usually": "forordinar",
        r"very": "gey",
        r"victims": "sittin` ducks",
        r"victim": "sittin` duck",
        r"views": "sichts",
        r"view": "sicht",
        r"was": "wis",
        r"wasn't": "wisna",
        r"wasnt": "wisna",
        r"walks": "daunders",
        r"walk": "daunder",
        r"walked": "daundered",
        r"walking": "daunderin",
        r"wall": "dyke",
        r"want": "waant",
        r"water": "watter",
        r"way": "wey",
        r"warden": "screw",
        r"well": "weel",
        r"were": "war",
        r"west": "wast",
        r"what": "whit",
        r"whatever": "whitevur",
        r"when": "whin",
        r"where": "whaur",
        r"whether": "whither",
        r"which": "whilk",
        r"who": "wha",
        r"whole": "hail",
        r"whom": "wham",
        r"whose": "wha`s",
        r"wife": "guidwife",
        r"wives": "guidwives",
        r"wind": "win`",
        r"window": "windae",
        r"windows": "windaes",
        r"with": "wi`",
        r"within": "wi`in",
        r"without": "wi`oot",
        r"woman": "wifie",
        r"women": "Wummin",
        r"work": "wirk",
        r"words": "Wurds",
        r"world": "warl",
        r"worldly": "war'ly",
        r"working": "wirkin",
        r"would": "wid",
        r"worse": "waur",
        r"ruined": "clapped",
        r"wrong": "wrang",
        r"yard": "yaird",
        r"yeah": "aye",
        r"True": ("aye", "oan"),
        r"yet": "yit",
        r"you": "ye",
        r"your": "yer",
        r"youre": "yer'r",
        r"yourself": "yersel`",
        r"quiet": "cannie",
        r"i": "a",
        r"ive": "a've",
        r"im": "a'm",
        r"it": "et",
        r"shit": "shite",
        r"shitsec": "shitesec",
        r"alright": "awricht",
        r"crazy": "doolally",
        r"idiot": ("eejit", "numpty", "mongo", "neep"),
        r"idiots": ("eejits", "numptys", "mongos", "neeps"),
        r"ugly": "hackit",
        r"tired": "knackert",
        r"gay": "bufty",
        r"testing": "testin`",
        r"fuck": "fook",
        r"fucking": "fookin`,feckin",
        r"fucker": "fooker",
        r"fuckers": "fookers",
        r"mom": ("maw", "mam"),
        r"moms": ("maws", "mams"),
        r"throw": "chuck",
        r"throwing": ("chuckin", "chuckin'"),
        r"threw": "chucked",
        r"fucked": ("fooked", "shagged"),
        r"ass": "arse",
        r"asses": "arses",
        r"bothered": "arsed",
        r"dick": "boaby",
        r"dicks": "boabys",
        r"something": "suhin",
        r"somethings": "suhins",
        r"boys": ("lads", "laddies"),
        r"girls": ("lasses", "lassies", "burds"),
    }

    PATTERNS = {
        DISCORD_MESSAGE_END: {
            # dynamic probability is broken
            " ye daft cunt": 0.5,  # lambda s: 0.4 + (0.6 * s / 9),
        }
    }


if __name__ == "__main__":
    with open("scotsman", "w") as f:
        for k, v in Scotsman.WORDS.items():
            if isinstance(v, tuple):
                print(
                    f"""\
Replacement::new(
    Source::Raw(r"\\b{k}\\b"),
    Box::new(MultiTarget {{
        replacement: vec![{", ".join(f'Box::new("{name}")' for name in v)}],
    }}),
),""",
                    file=f,
                )
            else:
                print(
                    f"""Replacement::new(Source::Raw(r"\\b{k}\\b"), Box::new("{v}"),),""",
                    file=f,
                )
