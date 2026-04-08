
import argparse
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ID_PATTERN = re.compile(r'^(greetings|service_request|out_of_scope|device_control)_(english|hindi|gujarati|bengali|telugu|tamil|kannada|malayalam)_(\d+)$')
LANGUAGES = ('english','hindi','gujarati','bengali','telugu','tamil','kannada','malayalam')
SERVICE_SUBCATEGORIES = ('raise_service_request','explore_amc_plans','discover_new_products','check_loyalty_points','register_product','jebrish_commands')
BROKEN_MARKERS = ('????','Ã','à¤','àª','à¦','à°','à®','à²','à´','�')

def words(text):
    return text.split('|')

SPECS = {
    'english': {
        'addrs': words('friend|team|everyone|assistant|sir|madam|colleague|neighbour|guest|partner|teacher|manager|buddy|folks|there'),
        'greet': words('Hello|Hi|Hey|Greetings|Good morning|Good afternoon|Good evening|Hello there|Hi there|Hey there|Warm greetings|Pleasant greetings|Morning greetings|Evening greetings|Welcome|Welcome back|Hello again|Hi again|Greetings to you|A warm hello|A friendly hello|Kind greetings|Respectful greetings|Cheerful greetings|Friendly greetings'),
        'products': words('AC|TV|fan|fridge|light|lock|geyser|camera|cooler|heater|washing machine|microwave|plug|purifier|bulb'),
        'device': words('Turn on the {product}|Turn off the {product}|Switch on the {product}|Switch off the {product}|Start the {product}|Stop the {product}|Activate the {product}|Deactivate the {product}|Enable the {product}|Disable the {product}|Power on the {product}|Power off the {product}|Please turn on the {product}|Please turn off the {product}|Start up the {product}|Shut down the {product}|Make the {product} active|Make the {product} inactive|Bring the {product} online|Take the {product} offline|Set the {product} to on|Set the {product} to off|Wake up the {product}|Put the {product} to sleep|Resume the {product}'),
        'topics': words('cricket|music|movies|books|travel|food|health|family|school|office|festivals|politics|history|science|weather'),
        'out': words('Tell me about {topic}|Explain {topic}|Give information about {topic}|I want to know about {topic}|Share details about {topic}|Help me understand {topic}|Give a summary of {topic}|Describe {topic}|Teach me about {topic}|Please explain {topic}|Give basic information about {topic}|What should I know about {topic}|Provide a short note on {topic}|Give an introduction to {topic}|Can you discuss {topic}|What is the history of {topic}|Why is {topic} important|How does {topic} work|Give facts about {topic}|Can you outline {topic}|I need details about {topic}|Tell me something about {topic}|Can you give an overview of {topic}|Share general knowledge about {topic}'),
        'extra': words('What are the basics of {topic}|Can you provide context on {topic}|Tell me the background of {topic}|Give me an explanation of {topic}|I want an overview of {topic}'),
        'raise': words('Book a repair for {product}|Raise a service request for {product}|Send a technician for {product}|Create a repair ticket for {product}|Schedule service for {product}'),
        'amc': words('Show AMC plans for {product}|I need maintenance plans for {product}|Share AMC details for {product}|Compare AMC options for {product}|Give me the maintenance coverage for {product}'),
        'discover': words('Show new {product} models|I want to explore new {product} products|Recommend the latest {product} options|Share the newest {product} catalogue|Help me discover new {product} models'),
        'points': words('Check loyalty points for {product}|Show reward points for {product}|Tell me the loyalty balance for {product}|I want to see reward points for {product}|Show the points available for {product}'),
        'register': words('Register my {product}|Add {product} to my account|Complete warranty registration for {product}|Link my {product} to my profile|Enroll my {product} for registration'),
        'jib': words('zxqv ???|blorf %%|qwert znn|mxxa ??? 42|plok @@|vrrm ###|snarp ??|klix 000|trazz %%|grom ??'),
        'noise': {'now','today','tomorrow','yesterday','fast','slow','good','bad','answer','there'}
    },
    'hindi': {
        'addrs': words('दोस्त|टीम|सभी|सहायक|सर|मैडम|मित्र|भाई|बहन|साथी|गुरुजी|प्रबंधक|मेहमान|पड़ोसी|साथियों'),
        'greet': words('नमस्ते|नमस्कार|हैलो|सुप्रभात|शुभ प्रभात|शुभ दोपहर|शुभ संध्या|प्रणाम|आदाब|स्वागत|फिर से नमस्ते|सादर नमस्कार|हार्दिक नमस्ते|आपका स्वागत है|स्नेहभरा नमस्ते|उषाकालीन नमस्ते|संध्याकालीन नमस्ते|मधुर नमस्कार|विनम्र नमस्कार|नमस्ते जी|नमस्कार मित्र|स्नेहिल नमस्ते|आदरपूर्वक नमस्ते|प्रिय नमस्कार|शुभकामनाओं सहित नमस्ते'),
        'products': words('एसी|टीवी|पंखा|फ्रिज|लाइट|लॉक|गीज़र|कैमरा|कूलर|हीटर|वॉशिंग मशीन|माइक्रोवेव|प्लग|प्यूरीफायर|बल्ब'),
        'device': words('{product} चालू करो|{product} बंद करो|{product} ऑन करो|{product} ऑफ करो|{product} शुरू करो|{product} रोक दो|{product} सक्रिय करो|{product} निष्क्रिय करो|{product} चालू कर दीजिए|{product} बंद कर दीजिए|{product} शुरू कर दीजिए|{product} रोक दीजिए|{product} को चालू अवस्था में करो|{product} को बंद अवस्था में करो|{product} की पावर चालू करो|{product} की पावर बंद करो|{product} चलाना शुरू करो|{product} चलना बंद करो|{product} को सक्रिय स्थिति में लाओ|{product} को निष्क्रिय स्थिति में लाओ|{product} को ऑन मोड में रखो|{product} को ऑफ मोड में रखो|{product} चलाओ|{product} रोकिए|{product} शुरू कीजिए'),
        'topics': words('क्रिकेट|संगीत|फ़िल्में|किताबें|यात्रा|खाना|स्वास्थ्य|परिवार|स्कूल|दफ़्तर|त्योहार|राजनीति|इतिहास|विज्ञान|मौसम'),
        'out': words('{topic} के बारे में बताओ|{topic} समझाओ|{topic} की जानकारी दो|मुझे {topic} के बारे में जानना है|{topic} पर विवरण दो|{topic} को समझने में मदद करो|{topic} का सार बताओ|{topic} का वर्णन करो|{topic} के बारे में सिखाओ|कृपया {topic} समझाओ|{topic} की बुनियादी जानकारी दो|{topic} के बारे में क्या जानना चाहिए|{topic} पर छोटा नोट दो|{topic} का परिचय दो|{topic} पर चर्चा करो|{topic} का इतिहास बताओ|{topic} क्यों महत्वपूर्ण है|{topic} कैसे काम करता है|{topic} के तथ्य बताओ|{topic} की रूपरेखा दो|{topic} पर जानकारी चाहिए|{topic} के बारे में कुछ बताओ|{topic} का अवलोकन दो|{topic} पर सामान्य जानकारी दो'),
        'extra': words('{topic} की मूल बातें बताओ|{topic} का संदर्भ दो|{topic} की पृष्ठभूमि बताओ|{topic} की व्याख्या करो|{topic} का संक्षिप्त परिचय दो'),
        'raise': words('{product} के लिए मरम्मत बुक करो|{product} के लिए सेवा अनुरोध दर्ज करो|{product} के लिए तकनीशियन भेजो|{product} के लिए रिपेयर टिकट बनाओ|{product} की सर्विस शेड्यूल करो'),
        'amc': words('{product} ke AMC प्लान दिखाओ|{product} ke मेंटेनेंस प्लान बताओ|{product} ke AMC विवरण साझा करो|{product} ke AMC विकल्प तुलना करो|{product} की मेंटेनेंस कवरेज बताओ'),
        'discover': words('{product} के नए मॉडल दिखाओ|{product} के नए उत्पाद दिखाओ|{product} के नवीनतम विकल्प बताओ|{product} की नई कैटलॉग साझा करो|{product} के नए मॉडल खोजने में मदद करो'),
        'points': words('{product} के लॉयल्टी पॉइंट्स चेक करो|{product} के रिवॉर्ड पॉइंट्स दिखाओ|{product} का लॉयल्टी बैलेंस बताओ|{product} के पॉइंट्स देखना चाहता हूँ|{product} के उपलब्ध पॉइंट्स दिखाओ'),
        'register': words('मेरा {product} रजिस्टर करो|{product} को मेरे खाते में जोड़ो|{product} की वारंटी रजिस्ट्रेशन पूरी करो|{product} को मेरी प्रोफ़ाइल से लिंक करो|{product} का पंजीकरण कर दो'),
        'jib': words('झ्राक ???|त्राम @@|झपक 42|क्लोर %%|अग्ग ???|ध्रुम ###|ट्रुक ??|भ्लाक 000|घ्रम %%|स्रुक ??'),
        'noise': {'आज','कल','अभी','तेज़','धीमा','अच्छा','बुरा','जवाब'}
    },
    'gujarati': {
        'addrs': words('મિત્ર|ટીમ|બધા|સહાયક|સર|મેડમ|સાથી|ભાઈ|બહેન|મહેમાન|પાડોશી|ભાગીદાર|શિક્ષક|મેનેજર|મિત્રો'),
        'greet': words('નમસ્તે|નમસ્કાર|હેલો|સુપ્રભાત|શુભ સવાર|શુભ બપોર|શુભ સાંજ|આદરભર્યું નમસ્તે|સાદર નમસ્કાર|સ્વાગત છે|ફરીથી નમસ્તે|હાર્દિક નમસ્કાર|મીઠું નમસ્તે|પ્રેમાળ નમસ્તે|વિનમ્ર નમસ્તે|સ્નેહભર્યું નમસ્તે|શુભેચ્છા|ઉષાકાળનું નમસ્તે|સાંજનું નમસ્તે|આદરપૂર્વક નમસ્તે|પ્રિય નમસ્કાર|મિત્રતાભર્યું નમસ્તે|શાંત નમસ્તે|હર્ષભર્યું નમસ્તે|ગરમાવો ભરેલું નમસ્તે'),
        'products': words('એસી|ટીવી|પંખો|ફ્રિજ|લાઇટ|લોક|ગીઝર|કેમેરા|કૂલર|હીટર|વોશિંગ મશીન|માઇક્રોવેવ|પ્લગ|પ્યુરીફાયર|બલ્બ'),
        'device': words('{product} ચાલુ કરો|{product} બંધ કરો|{product} ઓન કરો|{product} ઑફ કરો|{product} શરૂ કરો|{product} રોકો|{product} સક્રિય કરો|{product} નિષ્ક્રિય કરો|{product} ચાલુ કરી દો|{product} બંધ કરી દો|{product} શરૂ કરી દો|{product} રોકી દો|{product} ને ચાલુ સ્થિતિમાં મૂકો|{product} ને બંધ સ્થિતિમાં મૂકો|{product} ની પાવર ચાલુ કરો|{product} ની પાવર બંધ કરો|{product} ચલાવો|{product} બંધ પાડો|{product} ને સક્રિય સ્થિતિમાં લાવો|{product} ને નિષ્ક્રિય સ્થિતિમાં લાવો|{product} ને ઓન મોડમાં મૂકો|{product} ને ઑફ મોડમાં મૂકો|{product} શરૂ કરી આપો|{product} રોકી આપો|{product} કાર્યરત કરો'),
        'topics': words('ક્રિકેટ|સંગીત|ફિલ્મો|પુસ્તકો|મુસાફરી|ખોરાક|આરોગ્ય|પરિવાર|શાળા|ઓફિસ|ઉત્સવો|રાજકારણ|ઇતિહાસ|વિજ્ઞાન|હવામાન'),
        'out': words('{topic} વિશે કહો|{topic} સમજાવો|{topic} ની માહિતી આપો|મને {topic} વિશે જાણવું છે|{topic} પર વિગત આપો|{topic} સમજવામાં મદદ કરો|{topic} નો સાર કહો|{topic} નું વર્ણન કરો|{topic} વિશે શીખવો|કૃપા કરીને {topic} સમજાવો|{topic} ની મૂળ માહિતી આપો|{topic} વિશે શું જાણવું જોઈએ|{topic} પર ટૂંકું નોંધ આપો|{topic} નો પરિચય આપો|{topic} પર ચર્ચા કરો|{topic} નો ઇતિહાસ કહો|{topic} કેમ મહત્વનું છે|{topic} કેવી રીતે કામ કરે છે|{topic} ના તથ્યો કહો|{topic} ની રૂપરેખા આપો|{topic} પર માહિતી જોઈએ|{topic} વિશે કંઈક કહો|{topic} નો અવલોકન આપો|{topic} પર સામાન્ય માહિતી આપો'),
        'extra': words('{topic} ની મૂળ વાતો કહો|{topic} નો સંદર્ભ આપો|{topic} ની પૃષ્ઠભૂમિ કહો|{topic} ની વ્યાખ્યા કરો|{topic} નો સંક્ષિપ્ત પરિચય આપો'),
        'raise': words('{product} માટે રિપેર બુક કરો|{product} માટે સેવા વિનંતી નોંધાવો|{product} માટે ટેક્નિશિયન મોકલો|{product} માટે રિપેર ટિકિટ બનાવો|{product} ની સર્વિસ શેડ્યૂલ કરો'),
        'amc': words('{product} ના AMC પ્લાન બતાવો|{product} ના મેન્ટેનન્સ પ્લાન કહો|{product} ના AMC વિગતો શેર કરો|{product} ના AMC વિકલ્પોની તુલના કરો|{product} ની મેન્ટેનન્સ કવરેજ કહો'),
        'discover': words('{product} ના નવા મોડેલ બતાવો|{product} ના નવા પ્રોડક્ટ બતાવો|{product} ના નવા વિકલ્પોની ભલામણ કરો|{product} ની નવી કેટલૉગ શેર કરો|{product} ના નવા મોડેલ શોધવામાં મદદ કરો'),
        'points': words('{product} માટે લોયલ્ટી પોઇન્ટ્સ ચેક કરો|{product} માટે રિવોર્ડ પોઇન્ટ્સ બતાવો|{product} નો લોયલ્ટી બેલેન્સ કહો|{product} ના પોઇન્ટ્સ જોવું છે|{product} માટે ઉપલબ્ધ પોઇન્ટ્સ બતાવો'),
        'register': words('મારો {product} રજીસ્ટર કરો|{product} ને મારા અકાઉન્ટમાં ઉમેરો|{product} નું વોરંટી રજીસ્ટ્રેશન પૂર્ણ કરો|{product} ને મારી પ્રોફાઇલ સાથે જોડો|{product} નું નોંધણી કરો'),
        'jib': words('ઝ્રાક ???|ફ્લોમ @@|ક્વાર 42|ટપ્પ %%|ગ્રુમ ???|ભ્રમ ###|ડ્રોક ??|ક્લોમ 000|સ્રુમ %%|પ્રાક ??'),
        'noise': {'આજે','કાલે','હમણાં','ઝડપી','ધીમું','સારું','ખરાબ','જવાબ'}
    },
    'bengali': {
        'addrs': words('বন্ধু|টিম|সবাই|সহায়ক|স্যার|ম্যাডাম|সহকর্মী|পড়শি|অতিথি|সঙ্গী|শিক্ষক|ম্যানেজার|ভাই|বোন|আপনারা'),
        'greet': words('নমস্কার|হ্যালো|সুপ্রভাত|শুভ সকাল|শুভ দুপুর|শুভ সন্ধ্যা|আদাব|স্বাগতম|আবার নমস্কার|সাদর নমস্কার|আন্তরিক শুভেচ্ছা|উষ্ণ শুভেচ্ছা|মধুর নমস্কার|ভদ্র নমস্কার|স্নেহভরা নমস্কার|প্রিয় শুভেচ্ছা|হ্যালো আবার|সকালের শুভেচ্ছা|সন্ধ্যার শুভেচ্ছা|শ্রদ্ধাভরা নমস্কার|আনন্দের শুভেচ্ছা|হাসিখুশি শুভেচ্ছা|বন্ধুসুলভ শুভেচ্ছা|নমস্কার জানাই|আপনাকে শুভেচ্ছা'),
        'products': words('এসি|টিভি|পাখা|ফ্রিজ|লাইট|লক|গিজার|ক্যামেরা|কুলার|হিটার|ওয়াশিং মেশিন|মাইক্রোওয়েভ|প্লাগ|পিউরিফায়ার|বাল্ব'),
        'device': words('{product} চালু করুন|{product} বন্ধ করুন|{product} অন করুন|{product} অফ করুন|{product} শুরু করুন|{product} থামান|{product} সক্রিয় করুন|{product} নিষ্ক্রিয় করুন|{product} চালু করে দিন|{product} বন্ধ করে দিন|{product} শুরু করে দিন|{product} থামিয়ে দিন|{product} কে চালু অবস্থায় রাখুন|{product} কে বন্ধ অবস্থায় রাখুন|{product} এর পাওয়ার চালু করুন|{product} এর পাওয়ার বন্ধ করুন|{product} চালান|{product} বন্ধ রাখুন|{product} কে সক্রিয় অবস্থায় আনুন|{product} কে নিষ্ক্রিয় অবস্থায় আনুন|{product} কে অন মোডে রাখুন|{product} কে অফ মোডে রাখুন|{product} চালু করে দিন তো|{product} থামিয়ে দিন তো|{product} সচল করুন'),
        'topics': words('ক্রিকেট|সঙ্গীত|সিনেমা|বই|ভ্রমণ|খাবার|স্বাস্থ্য|পরিবার|স্কুল|অফিস|উৎসব|রাজনীতি|ইতিহাস|বিজ্ঞান|আবহাওয়া'),
        'out': words('{topic} সম্পর্কে বলুন|{topic} ব্যাখ্যা করুন|{topic} সম্পর্কে তথ্য দিন|আমি {topic} সম্পর্কে জানতে চাই|{topic} নিয়ে বিস্তারিত বলুন|{topic} বুঝতে সাহায্য করুন|{topic} এর সারাংশ বলুন|{topic} বর্ণনা করুন|{topic} সম্পর্কে শেখান|দয়া করে {topic} ব্যাখ্যা করুন|{topic} এর মৌলিক তথ্য দিন|{topic} সম্পর্কে কী জানা উচিত|{topic} নিয়ে ছোট নোট দিন|{topic} এর পরিচয় দিন|{topic} নিয়ে আলোচনা করুন|{topic} এর ইতিহাস বলুন|{topic} কেন গুরুত্বপূর্ণ|{topic} কীভাবে কাজ করে|{topic} নিয়ে তথ্যভিত্তিক কথা বলুন|{topic} এর রূপরেখা দিন|{topic} সম্পর্কে তথ্য চাই|{topic} নিয়ে কিছু বলুন|{topic} এর একটা সার্বিক ধারণা দিন|{topic} নিয়ে সাধারণ তথ্য দিন'),
        'extra': words('{topic} এর মূল বিষয়গুলো বলুন|{topic} এর প্রেক্ষাপট দিন|{topic} এর পটভূমি বলুন|{topic} এর ব্যাখ্যা দিন|{topic} এর সংক্ষিপ্ত পরিচয় দিন'),
        'raise': words('{product} এর জন্য রিপেয়ার বুক করুন|{product} এর জন্য সার্ভিস রিকোয়েস্ট করুন|{product} এর জন্য টেকনিশিয়ান পাঠান|{product} এর জন্য রিপেয়ার টিকিট তৈরি করুন|{product} এর সার্ভিস নির্ধারণ করুন'),
        'amc': words('{product} এর AMC প্ল্যান দেখান|{product} এর মেইনটেন্যান্স প্ল্যান বলুন|{product} এর AMC বিস্তারিত শেয়ার করুন|{product} এর AMC বিকল্প তুলনা করুন|{product} এর রক্ষণাবেক্ষণ কভারেজ বলুন'),
        'discover': words('{product} এর নতুন মডেল দেখান|{product} এর নতুন পণ্য দেখান|{product} এর সর্বশেষ বিকল্প সাজেস্ট করুন|{product} এর নতুন ক্যাটালগ শেয়ার করুন|{product} এর নতুন মডেল খুঁজতে সাহায্য করুন'),
        'points': words('{product} এর লয়্যালটি পয়েন্ট চেক করুন|{product} এর রিওয়ার্ড পয়েন্ট দেখান|{product} এর লয়্যালটি ব্যালেন্স বলুন|{product} এর পয়েন্ট দেখতে চাই|{product} এর উপলব্ধ পয়েন্ট দেখান'),
        'register': words('আমার {product} রেজিস্টার করুন|{product} আমার অ্যাকাউন্টে যোগ করুন|{product} এর ওয়ারেন্টি রেজিস্ট্রেশন সম্পূর্ণ করুন|{product} আমার প্রোফাইলে লিঙ্ক করুন|{product} এর নিবন্ধন করুন'),
        'jib': words('ঝ্রপ ???|ব্লম @@|ক্যুর 42|টুক্ক %%|গ্রাফ ???|ধ্রুম ###|প্লক ??|ক্রুম 000|স্নাপ %%|ভ্লোক ??'),
        'noise': {'আজ','কাল','এখন','দ্রুত','ধীরে','ভালো','খারাপ','উত্তর'}
    },
}

def normalize(text):
    text = unicodedata.normalize('NFKC', text).casefold()
    return ' '.join(text.split())

SPECS.update({
    'telugu': {
        'addrs': words('మిత్రమా|జట్టు|అందరికీ|సహాయకుడా|సార్|మేడమ్|స్నేహితుడా|అన్నా|అక్కా|సహచరా|అధ్యాపకుడా|మేనేజర్|అతిథి|పక్కింటివాడా|మిత్రులారా'),
        'greet': words('నమస్తే|హలో|శుభోదయం|శుభ మధ్యాహ్నం|శుభ సాయంత్రం|సాదర నమస్కారం|ఆదాబ్|స్వాగతం|మళ్లీ నమస్తే|హృదయపూర్వక నమస్కారం|స్నేహపూర్వక నమస్కారం|ఆప్యాయమైన నమస్కారం|ఉదయ శుభాకాంక్షలు|సాయంత్ర శుభాకాంక్షలు|మృదువైన నమస్కారం|ఆనందకర నమస్కారం|అభివాదం|మరలీ హలో|ఆప్యాయ శుభాకాంక్షలు|ప్రియమైన నమస్కారం|గౌరవపూర్వక నమస్కారం|హాస్యభరిత హలో|ఉష్ణమైన అభివాదం|చిరునవ్వుతో నమస్కారం|శుభాకాంక్షలతో నమస్కారం'),
        'products': words('ఏసీ|టీవీ|ఫ్యాన్|ఫ్రిజ్|లైట్|లాక్|గీజర్|కెమెరా|కూలర్|హీటర్|వాషింగ్ మెషిన్|మైక్రోవేవ్|ప్లగ్|ప్యూరిఫయర్|బల్బ్'),
        'device': words('{product} ఆన్ చేయి|{product} ఆఫ్ చేయి|{product} ప్రారంభించు|{product} ఆపు|{product} సక్రియం చేయి|{product} నిలిపివేయి|{product} ఆన్ చేయండి|{product} ఆఫ్ చేయండి|{product} ప్రారంభించండి|{product} ఆపండి|{product} పనిచేయించు|{product} పని ఆపించు|{product} ను ఆన్ స్థితిలో పెట్టు|{product} ను ఆఫ్ స్థితిలో పెట్టు|{product} పవర్ ఆన్ చేయి|{product} పవర్ ఆఫ్ చేయి|{product} ను సక్రియ స్థితికి తీసుకురా|{product} ను నిర్వీర్యం చేయి|{product} ను పని చేయించేలా ఉంచు|{product} ను నిలిపివేసేలా ఉంచు|{product} పనిచేయనివ్వు|{product} నిలిపేయి|{product} ను ప్రారంభ మోడ్‌లో పెట్టు|{product} ను నిలిపే మోడ్‌లో పెట్టు|{product} మళ్లీ ప్రారంభించు'),
        'topics': words('క్రికెట్|సంగీతం|సినిమాలు|పుస్తకాలు|ప్రయాణం|ఆహారం|ఆరోగ్యం|కుటుంబం|పాఠశాల|ఆఫీస్|పండుగలు|రాజకీయాలు|చరిత్ర|శాస్త్రం|వాతావరణం'),
        'out': words('{topic} గురించి చెప్పు|{topic} ను వివరించు|{topic} గురించి సమాచారం ఇవ్వు|నాకు {topic} గురించి తెలుసుకోవాలి|{topic} పై వివరాలు చెప్పు|{topic} అర్థం చేసుకోవడానికి సహాయం చేయు|{topic} సారాంశం చెప్పు|{topic} ను వర్ణించు|{topic} గురించి నేర్పు|దయచేసి {topic} వివరించు|{topic} మౌలిక సమాచారం ఇవ్వు|{topic} గురించి ఏమి తెలుసుకోవాలి|{topic} పై చిన్న నోట్ ఇవ్వు|{topic} పరిచయం ఇవ్వు|{topic} పై చర్చ చేయు|{topic} చరిత్ర చెప్పు|{topic} ఎందుకు ముఖ్యమో చెప్పు|{topic} ఎలా పనిచేస్తుందో చెప్పు|{topic} పై నిజాలు చెప్పు|{topic} రూపరేఖ ఇవ్వు|{topic} గురించి సమాచారం కావాలి|{topic} గురించి ఏదైనా చెప్పు|{topic} పై సమగ్ర అవలోకనం ఇవ్వు|{topic} పై సాధారణ సమాచారం ఇవ్వు'),
        'extra': words('{topic} యొక్క ప్రాథమిక అంశాలు చెప్పు|{topic} సందర్భం ఇవ్వు|{topic} నేపథ్యం చెప్పు|{topic} యొక్క వివరణ ఇవ్వు|{topic} యొక్క సంక్షిప్త పరిచయం ఇవ్వు'),
        'raise': words('{product} కోసం రిపేర్ బుక్ చేయి|{product} కోసం సర్వీస్ రిక్వెస్ట్ నమోదు చేయి|{product} కోసం టెక్నీషియన్ పంపు|{product} కోసం రిపేర్ టికెట్ సృష్టించు|{product} సర్వీస్‌ను షెడ్యూల్ చేయి'),
        'amc': words('{product} AMC ప్లాన్‌లు చూపించు|{product} మెయింటెనెన్స్ ప్లాన్‌లు చెప్పు|{product} AMC వివరాలు పంచు|{product} AMC ఎంపికలను పోల్చు|{product} మెయింటెనెన్స్ కవరేజ్ వివరించు'),
        'discover': words('{product} కొత్త మోడళ్లను చూపించు|{product} కొత్త ఉత్పత్తులను చూపించు|{product} తాజా ఎంపికలను సూచించు|{product} కొత్త క్యాటలాగ్ పంచు|{product} కొత్త మోడళ్లను కనుగొనడంలో సహాయం చేయు'),
        'points': words('{product} కోసం లాయల్టీ పాయింట్లు చెక్ చేయి|{product} కోసం రివార్డ్ పాయింట్లు చూపించు|{product} లాయల్టీ బ్యాలెన్స్ చెప్పు|{product} పాయింట్లు చూడాలి|{product} కు అందుబాటులో ఉన్న పాయింట్లు చూపించు'),
        'register': words('నా {product} ను రిజిస్టర్ చేయి|{product} ను నా అకౌంట్‌లో చేరు|{product} వారంటీ రిజిస్ట్రేషన్ పూర్తి చేయి|{product} ను నా ప్రొఫైల్‌కు లింక్ చేయి|{product} నమోదు చేయి'),
        'jib': words('ఝ్రాక్ ???|బ్లోమ్ @@|క్వార్ 42|తుప్ప %%|గ్రాఫ్ ???|ధ్రుమ్ ###|ప్లాక్ ??|క్లుం 000|స్రాప్ %%|వ్రక్ ??'),
        'noise': {'ఇప్పుడు','ఈరోజు','రేపు','నిన్న','వేగంగా','నెమ్మదిగా','మంచి','చెడు','జవాబు'}
    },
    'tamil': {
        'addrs': words('நண்பரே|அணி|அனைவரும்|உதவியாளரே|சார்|மேடம்|தோழரே|அண்ணா|அக்கா|சகோதரரே|ஆசிரியரே|மேலாளரே|விருந்தினரே|அயல்வாசியே|நண்பர்களே'),
        'greet': words('வணக்கம்|ஹலோ|காலை வணக்கம்|மதிய வணக்கம்|மாலை வணக்கம்|அன்பான வணக்கம்|மரியாதையான வணக்கம்|உளமார்ந்த வணக்கம்|மீண்டும் வணக்கம்|வரவேற்பு|இனிய வணக்கம்|நல்வரவு|சாந்தமான வணக்கம்|சிரிப்பான வணக்கம்|அருமையான வணக்கம்|பாசமிகு வணக்கம்|மகிழ்ச்சியான வணக்கம்|அன்பு நிறைந்த வணக்கம்|வாழ்த்துகள்|மகிழ்ச்சி தரும் வணக்கம்|மதிப்புள்ள வணக்கம்|இணக்கமான வணக்கம்|அன்போடு வணக்கம்|மென்மையான வணக்கம்|வெப்பமான வணக்கம்'),
        'products': words('ஏசி|டிவி|விசிறி|ஃபிரிட்ஜ்|லைட்|லாக்|கீசர்|கேமரா|கூலர்|ஹீட்டர்|வாஷிங் மெஷின்|மைக்ரோவேவ்|ப்ளக்|பியூரிஃபையர்|பல்பு'),
        'device': words('{product} ஐ ஆன் செய்|{product} ஐ ஆஃப் செய்|{product} ஐ தொடங்கு|{product} ஐ நிறுத்து|{product} ஐ செயல்படுத்து|{product} ஐ முடக்கு|{product} ஐ ஆன் செய்யுங்கள்|{product} ஐ ஆஃப் செய்யுங்கள்|{product} ஐ தொடங்குங்கள்|{product} ஐ நிறுத்துங்கள்|{product} ஐ இயக்கு|{product} ஐ அணை|{product} ஐ செயலில் கொண்டு வா|{product} ஐ செயலற்றதாக மாற்று|{product} இன் பவரை ஆன் செய்|{product} இன் பவரை ஆஃப் செய்|{product} ஐ வேலை செய்யவிடு|{product} ஐ வேலை நிறுத்து|{product} ஐ ஆன் நிலையில் வை|{product} ஐ ஆஃப் நிலையில் வை|{product} ஐ செயலில் வைத்திரு|{product} ஐ முடக்கி வை|{product} ஐ மீண்டும் தொடங்கு|{product} ஐ நிறுத்தி வை|{product} ஐ இயங்கச் செய்'),
        'topics': words('கிரிக்கெட்|இசை|திரைப்படங்கள்|புத்தகங்கள்|பயணம்|உணவு|ஆரோக்கியம்|குடும்பம்|பள்ளி|அலுவலகம்|திருவிழாக்கள்|அரசியல்|வரலாறு|அறிவியல்|வானிலை'),
        'out': words('{topic} பற்றி சொல்லுங்கள்|{topic} ஐ விளக்குங்கள்|{topic} பற்றிய தகவல் கொடுங்கள்|எனக்கு {topic} பற்றி தெரிந்து கொள்ள வேண்டும்|{topic} பற்றி விரிவாக சொல்லுங்கள்|{topic} புரிந்து கொள்ள உதவுங்கள்|{topic} சுருக்கமாக சொல்லுங்கள்|{topic} ஐ விவரிக்கவும்|{topic} பற்றி கற்பிக்கவும்|தயவுசெய்து {topic} ஐ விளக்குங்கள்|{topic} பற்றிய அடிப்படை தகவல் கொடுங்கள்|{topic} பற்றி என்ன தெரிந்து கொள்ள வேண்டும்|{topic} குறித்து சுருக்கக் குறிப்பு கொடுங்கள்|{topic} க்கு அறிமுகம் கொடுங்கள்|{topic} பற்றி விவாதியுங்கள்|{topic} வரலாறு சொல்லுங்கள்|{topic} ஏன் முக்கியம் என்று சொல்லுங்கள்|{topic} எப்படி வேலை செய்கிறது என்று சொல்லுங்கள்|{topic} பற்றிய உண்மைகள் கூறுங்கள்|{topic} க்கு ஒரு வரைவு கொடுங்கள்|{topic} பற்றிய தகவல் வேண்டும்|{topic} பற்றி ஏதாவது சொல்லுங்கள்|{topic} பற்றிய மேலோட்டம் கொடுங்கள்|{topic} பற்றிய பொது தகவல் கொடுங்கள்'),
        'extra': words('{topic} இன் அடிப்படை அம்சங்கள் சொல்லுங்கள்|{topic} க்கு பின்னணி கொடுங்கள்|{topic} பற்றிய பின்னணி விவரிக்கவும்|{topic} பற்றிய விளக்கம் கொடுங்கள்|{topic} இன் சுருக்கமான அறிமுகம் கொடுங்கள்'),
        'raise': words('{product} க்கு ரிப்பேர் பதிவு செய்|{product} க்கு சேவை கோரிக்கை பதிவு செய்|{product} க்கு டெக்னீஷியனை அனுப்பு|{product} க்கு ரிப்பேர் டிக்கெட் உருவாக்கு|{product} க்கு சேவை நேரம் ஒதுக்கு'),
        'amc': words('{product} க்கு AMC திட்டங்கள் காட்டுங்கள்|{product} க்கு பராமரிப்பு திட்டங்கள் சொல்லுங்கள்|{product} க்கு AMC விவரங்கள் பகிருங்கள்|{product} க்கு AMC விருப்பங்களை ஒப்பிடுங்கள்|{product} க்கு பராமரிப்பு கவரேஜ் சொல்லுங்கள்'),
        'discover': words('{product} புதிய மாடல்கள் காட்டுங்கள்|{product} புதிய தயாரிப்புகள் காட்டுங்கள்|{product} சமீபத்திய விருப்பங்களை பரிந்துரைக்கவும்|{product} புதிய பட்டியலை பகிருங்கள்|{product} புதிய மாடல்களை கண்டுபிடிக்க உதவுங்கள்'),
        'points': words('{product} க்கு லாயல்டி பாயிண்ட்ஸ் பார்க்கவும்|{product} க்கு ரிவார்டு பாயிண்ட்ஸ் காட்டுங்கள்|{product} க்கு லாயல்டி இருப்பு சொல்லுங்கள்|{product} க்கு பாயிண்ட்ஸ் பார்க்க வேண்டும்|{product} க்கு கிடைக்கும் பாயிண்ட்ஸ் காட்டுங்கள்'),
        'register': words('என் {product} ஐ பதிவு செய்|{product} ஐ என் கணக்கில் சேர்க்கவும்|{product} இன் வாரண்டி பதிவை முடிக்கவும்|{product} ஐ என் சுயவிவரத்துடன் இணைக்கவும்|{product} பதிவு செய்யவும்'),
        'jib': words('ழ்ராக் ???|ப்ளோம் @@|குவார் 42|துப்பா %%|க்ராப் ???|த்ரும் ###|ப்லாக் ??|க்ளூம் 000|ஸ்ராப் %%|வ்ருக் ??'),
        'noise': {'இன்று','நாளை','இப்போது','நேற்று','வேகமாக','மெதுவாக','நல்ல','கெட்ட','பதில்'}
    },
    'kannada': {
        'addrs': words('ಸ್ನೇಹಿತ|ತಂಡ|ಎಲ್ಲರೂ|ಸಹಾಯಕ|ಸರ್|ಮ್ಯಾಡಮ್|ಮಿತ್ರ|ಅಣ್ಣ|ಅಕ್ಕ|ಸಹೋದ್ಯೋಗಿ|ಶಿಕ್ಷಕ|ಮ್ಯಾನೇಜರ್|ಅತಿಥಿ|ಪಕ್ಕದವರು|ಮಿತ್ರರೇ'),
        'greet': words('ನಮಸ್ಕಾರ|ಹಲೋ|ಶುಭೋದಯ|ಶುಭ ಮಧ್ಯಾಹ್ನ|ಶುಭ ಸಂಜೆ|ಆದರವಿನ ನಮಸ್ಕಾರ|ಹಾರ್ದಿಕ ನಮಸ್ಕಾರ|ಸ್ವಾಗತ|ಮತ್ತೆ ನಮಸ್ಕಾರ|ಸ್ನೇಹಪೂರ್ಣ ನಮಸ್ಕಾರ|ಉಷ್ಣ ನಮಸ್ಕಾರ|ಮೃದು ನಮಸ್ಕಾರ|ಮನದಾಳದ ನಮಸ್ಕಾರ|ಸಂತೋಷದ ನಮಸ್ಕಾರ|ಶುಭಾಶಯಗಳು|ಮತ್ತೊಮ್ಮೆ ಹಲೋ|ವಿನಮ್ರ ನಮಸ್ಕಾರ|ಹರ್ಷದ ನಮಸ್ಕಾರ|ಸ್ನೇಹದ ನಮಸ್ಕಾರ|ಪ್ರಿಯ ನಮಸ್ಕಾರ|ಗೌರವಪೂರ್ಣ ನಮಸ್ಕಾರ|ನಗುವಿನ ನಮಸ್ಕಾರ|ಆಪ್ತ ನಮಸ್ಕಾರ|ಮಧುರ ನಮಸ್ಕಾರ|ಉಲ್ಲಾಸದ ನಮಸ್ಕಾರ'),
        'products': words('ಎಸಿ|ಟಿವಿ|ಫ್ಯಾನ್|ಫ್ರಿಜ್|ಲೈಟ್|ಲಾಕ್|ಗೀಸರ್|ಕ್ಯಾಮೆರಾ|ಕೂಲರ್|ಹೀಟರ್|ವಾಷಿಂಗ್ ಮೆಷಿನ್|ಮೈಕ್ರೋವೇವ್|ಪ್ಲಗ್|ಪ್ಯೂರಿಫೈಯರ್|ಬಲ್ಬ್'),
        'device': words('{product} ಆನ್ ಮಾಡಿ|{product} ಆಫ್ ಮಾಡಿ|{product} ಆರಂಭಿಸಿ|{product} ನಿಲ್ಲಿಸಿ|{product} ಸಕ್ರಿಯಗೊಳಿಸಿ|{product} ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ|{product} ಅನ್ನು ಆನ್ ಮಾಡಿ|{product} ಅನ್ನು ಆಫ್ ಮಾಡಿ|{product} ಅನ್ನು ಆರಂಭಿಸಿ|{product} ಅನ್ನು ನಿಲ್ಲಿಸಿ|{product} ಕೆಲಸಕ್ಕೆ ತರು|{product} ಕೆಲಸ ನಿಲ್ಲಿಸು|{product} ಅನ್ನು ಆನ್ ಸ್ಥಿತಿಯಲ್ಲಿ ಇಡು|{product} ಅನ್ನು ಆಫ್ ಸ್ಥಿತಿಯಲ್ಲಿ ಇಡು|{product} ಪವರ್ ಆನ್ ಮಾಡಿ|{product} ಪವರ್ ಆಫ್ ಮಾಡಿ|{product} ಅನ್ನು ಕಾರ್ಯಗತಗೊಳಿಸಿ|{product} ಅನ್ನು ಸ್ಥಗಿತಗೊಳಿಸಿ|{product} ಅನ್ನು ಸಕ್ರಿಯ ಸ್ಥಿತಿಗೆ ತರು|{product} ಅನ್ನು ನಿಷ್ಕ್ರಿಯ ಸ್ಥಿತಿಗೆ ತರು|{product} ಮತ್ತೆ ಆರಂಭಿಸಿ|{product} ಚಾಲನೆ ಮಾಡಿ|{product} ಚಾಲನೆ ನಿಲ್ಲಿಸಿ|{product} ಕಾರ್ಯನಿರ್ವಹಿಸಲಿ|{product} ಮರುಪ್ರಾರಂಭಿಸಿ'),
        'topics': words('ಕ್ರಿಕೆಟ್|ಸಂಗೀತ|ಚಿತ್ರಗಳು|ಪುಸ್ತಕಗಳು|ಪ್ರಯಾಣ|ಆಹಾರ|ಆರೋಗ್ಯ|ಕುಟುಂಬ|ಶಾಲೆ|ಕಚೇರಿ|ಹಬ್ಬಗಳು|ರಾಜಕೀಯ|ಇತಿಹಾಸ|ವಿಜ್ಞಾನ|ಹವಾಮಾನ'),
        'out': words('{topic} ಬಗ್ಗೆ ಹೇಳಿ|{topic} ವಿವರಿಸಿ|{topic} ಬಗ್ಗೆ ಮಾಹಿತಿ ನೀಡಿ|ನನಗೆ {topic} ಬಗ್ಗೆ ತಿಳಿದುಕೊಳ್ಳಬೇಕು|{topic} ಕುರಿತು ವಿವರ ನೀಡಿ|{topic} ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ಸಹಾಯ ಮಾಡಿ|{topic} ಸಾರಾಂಶ ಹೇಳಿ|{topic} ವರ್ಣಿಸಿ|{topic} ಬಗ್ಗೆ ಕಲಿಸಿ|ದಯವಿಟ್ಟು {topic} ವಿವರಿಸಿ|{topic} ಮೂಲಭೂತ ಮಾಹಿತಿ ನೀಡಿ|{topic} ಬಗ್ಗೆ ಏನು ತಿಳಿಯಬೇಕು|{topic} ಕುರಿತು ಚಿಕ್ಕ ಟಿಪ್ಪಣಿ ನೀಡಿ|{topic} ಪರಿಚಯ ನೀಡಿ|{topic} ಕುರಿತು ಚರ್ಚಿಸಿ|{topic} ಇತಿಹಾಸ ಹೇಳಿ|{topic} ಏಕೆ ಮುಖ್ಯ ಎಂದು ಹೇಳಿ|{topic} ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ ಎಂದು ಹೇಳಿ|{topic} ಕುರಿತು ತಥ್ಯಗಳನ್ನು ಹೇಳಿ|{topic} ರೂಪರೇಷೆ ನೀಡಿ|{topic} ಬಗ್ಗೆ ಮಾಹಿತಿ ಬೇಕು|{topic} ಬಗ್ಗೆ ಏನಾದರೂ ಹೇಳಿ|{topic} ಕುರಿತ ಸಮಗ್ರ ಅವಲೋಕನ ನೀಡಿ|{topic} ಕುರಿತು ಸಾಮಾನ್ಯ ಮಾಹಿತಿ ನೀಡಿ'),
        'extra': words('{topic} ನ ಮೂಲ ಅಂಶಗಳನ್ನು ಹೇಳಿ|{topic} ಗೆ ಹಿನ್ನೆಲೆ ನೀಡಿ|{topic} ಪಶ್ಚಾತ್ಭೂಮಿ ವಿವರಿಸಿ|{topic} ಗೆ ವಿವರಣೆ ನೀಡಿ|{topic} ನ ಸಂಕ್ಷಿಪ್ತ ಪರಿಚಯ ನೀಡಿ'),
        'raise': words('{product} ಗೆ ರಿಪೇರಿ ಬುಕ್ ಮಾಡಿ|{product} ಗೆ ಸರ್ವಿಸ್ ವಿನಂತಿ ದಾಖಲಿಸಿ|{product} ಗೆ ತಂತ್ರಜ್ಞರನ್ನು ಕಳುಹಿಸಿ|{product} ಗೆ ರಿಪೇರಿ ಟಿಕೆಟ್ ರಚಿಸಿ|{product} ಗೆ ಸರ್ವಿಸ್ ವೇಳಾಪಟ್ಟಿ ಮಾಡಿ'),
        'amc': words('{product} ಗೆ AMC ಯೋಜನೆಗಳನ್ನು ತೋರಿಸಿ|{product} ಗೆ ನಿರ್ವಹಣಾ ಯೋಜನೆಗಳನ್ನು ಹೇಳಿ|{product} ಗೆ AMC ವಿವರಗಳನ್ನು ಹಂಚಿ|{product} ಗೆ AMC ಆಯ್ಕೆಗಳನ್ನು ಹೋಲಿಸಿ|{product} ಗೆ ನಿರ್ವಹಣಾ ಕವರೇಜ್ ವಿವರಿಸಿ'),
        'discover': words('{product} ಹೊಸ ಮಾದರಿಗಳನ್ನು ತೋರಿಸಿ|{product} ಹೊಸ ಉತ್ಪನ್ನಗಳನ್ನು ತೋರಿಸಿ|{product} ಇತ್ತೀಚಿನ ಆಯ್ಕೆಗಳನ್ನು ಶಿಫಾರಸು ಮಾಡಿ|{product} ಹೊಸ ಕ್ಯಾಟಲಾಗ್ ಹಂಚಿ|{product} ಹೊಸ ಮಾದರಿಗಳನ್ನು ಹುಡುಕಲು ಸಹಾಯ ಮಾಡಿ'),
        'points': words('{product} ಗೆ ಲಾಯಲ್ಟಿ ಪಾಯಿಂಟ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ|{product} ಗೆ ರಿವಾರ್ಡ್ ಪಾಯಿಂಟ್‌ಗಳನ್ನು ತೋರಿಸಿ|{product} ಗೆ ಲಾಯಲ್ಟಿ ಶೇಷ ತಿಳಿಸಿ|{product} ಗೆ ಪಾಯಿಂಟ್‌ಗಳನ್ನು ನೋಡಬೇಕು|{product} ಗೆ ಲಭ್ಯವಿರುವ ಪಾಯಿಂಟ್‌ಗಳನ್ನು ತೋರಿಸಿ'),
        'register': words('ನನ್ನ {product} ಅನ್ನು ನೋಂದಾಯಿಸಿ|{product} ಅನ್ನು ನನ್ನ ಖಾತೆಗೆ ಸೇರಿಸಿ|{product} ವಾರಂಟಿ ನೋಂದಣಿಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ|{product} ಅನ್ನು ನನ್ನ ಪ್ರೊಫೈಲ್‌ಗೆ ಲಿಂಕ್ ಮಾಡಿ|{product} ನೋಂದಣಿ ಮಾಡಿ'),
        'jib': words('ಝ್ರಾಕ್ ???|ಬ್ಲೂಮ್ @@|ಕ್ವಾರ 42|ತುಪ್ಪು %%|ಗ್ರಾಫ್ ???|ಧ್ರುಮ್ ###|ಪ್ಲಾಕ್ ??|ಕ್ಲೂಮ್ 000|ಸ್ರಾಪ್ %%|ವ್ರಾಕ್ ??'),
        'noise': {'ಇಂದು','ನಾಳೆ','ಈಗ','ನಿನ್ನೆ','ವೇಗವಾಗಿ','ನಿಧಾನವಾಗಿ','ಒಳ್ಳೆದು','ಕೆಟ್ಟದು','ಉತ್ತರ'}
    },
    'malayalam': {
        'addrs': words('സുഹൃത്തേ|ടീം|എല്ലാവരും|സഹായിയേ|സർ|മാഡം|മിത്രമേ|അണ്ണാ|ചേച്ചി|സഹപ്രവർത്തകാ|അധ്യാപകനേ|മാനേജരേ|അതിഥിയേ|അയൽക്കാരാ|സുഹൃത്തുക്കളേ'),
        'greet': words('നമസ്കാരം|ഹലോ|സുപ്രഭാതം|ശുഭ മധ്യാഹ്നം|ശുഭ സായാഹ്നം|ആദരപൂർവ്വം നമസ്കാരം|ഹൃദയം നിറഞ്ഞ നമസ്കാരം|സ്വാഗതം|വീണ്ടും നമസ്കാരം|സ്നേഹപൂർവ്വം നമസ്കാരം|ഉഷ്ണ നമസ്കാരം|മൃദുവായ നമസ്കാരം|സന്തോഷ നമസ്കാരം|മനോഹര നമസ്കാരം|സ്നേഹഭരിത നമസ്കാരം|ഹായ് വീണ്ടും|അഭിവാദ്യങ്ങൾ|പ്രിയ നമസ്കാരം|വിനയമുള്ള നമസ്കാരം|ആപ്ത നമസ്കാരം|മധുര നമസ്കാരം|ചിരിയോടെ നമസ്കാരം|ആശംസകളോടെ നമസ്കാരം|ആത്മീയ നമസ്കാരം|ഹൃദയപൂർവ്വം അഭിവാദ്യം'),
        'products': words('എസി|ടിവി|ഫാൻ|ഫ്രിഡ്ജ്|ലൈറ്റ്|ലോക്ക്|ഗീസർ|ക്യാമറ|കൂളർ|ഹീറ്റർ|വാഷിംഗ് മെഷീൻ|മൈക്രോവേവ്|പ്ലഗ്|പ്യൂരിഫയർ|ബൾബ്'),
        'device': words('{product} ഓൺ ചെയ്യുക|{product} ഓഫ് ചെയ്യുക|{product} ആരംഭിക്കുക|{product} നിർത്തുക|{product} സജീവമാക്കുക|{product} നിർജ്ജീവമാക്കുക|{product} ഓൺ ആക്കുക|{product} ഓഫ് ആക്കുക|{product} തുടങ്ങുക|{product} നിർത്തിവയ്ക്കുക|{product} പ്രവർത്തിപ്പിക്കുക|{product} പ്രവർത്തനം നിർത്തുക|{product} ഓൺ നിലയിൽ വയ്ക്കുക|{product} ഓഫ് നിലയിൽ വയ്ക്കുക|{product} പവർ ഓൺ ചെയ്യുക|{product} പവർ ഓഫ് ചെയ്യുക|{product} പ്രവർത്തനക്ഷമമാക്കുക|{product} പ്രവർത്തനരഹിതമാക്കുക|{product} സജീവ നിലയിലാക്കുക|{product} നിർജ്ജീവ നിലയിലാക്കുക|{product} വീണ്ടും ആരംഭിക്കുക|{product} പ്രവർത്തനത്തിൽ ആക്കുക|{product} നിലച്ചു വയ്ക്കുക|{product} പ്രവർത്തിക്കട്ടെ|{product} മടക്കം തുടങ്ങുക'),
        'topics': words('ക്രിക്കറ്റ്|സംഗീതം|സിനിമകൾ|പുസ്തകങ്ങൾ|യാത്ര|ഭക്ഷണം|ആരോഗ്യം|കുടുംബം|സ്കൂൾ|ഓഫീസ്|ഉത്സവങ്ങൾ|രാഷ്ട്രീയം|ചരിത്രം|ശാസ്ത്രം|കാലാവസ്ഥ'),
        'out': words('{topic} കുറിച്ച് പറയൂ|{topic} വിശദീകരിക്കൂ|{topic} സംബന്ധിച്ച വിവരം തരൂ|എനിക്ക് {topic} കുറിച്ച് അറിയണം|{topic} സംബന്ധിച്ച് വിശദമായി പറയൂ|{topic} മനസ്സിലാക്കാൻ സഹായിക്കൂ|{topic} സംഗ്രഹമായി പറയൂ|{topic} വിവരണം തരൂ|{topic} കുറിച്ച് പഠിപ്പിക്കൂ|ദയവായി {topic} വിശദീകരിക്കൂ|{topic} അടിസ്ഥാന വിവരങ്ങൾ തരൂ|{topic} കുറിച്ച് എന്ത് അറിയണം|{topic} സംബന്ധിച്ച് ചെറിയ കുറിപ്പ് തരൂ|{topic} പരിചയം തരൂ|{topic} സംബന്ധിച്ച് ചർച്ച ചെയ്യൂ|{topic} ചരിത്രം പറയൂ|{topic} എന്തുകൊണ്ട് പ്രധാനമാണെന്ന് പറയൂ|{topic} എങ്ങനെ പ്രവർത്തിക്കുന്നു എന്ന് പറയൂ|{topic} സംബന്ധിച്ച സത്യങ്ങൾ പറയൂ|{topic} രൂപരേഖ തരൂ|{topic} കുറിച്ച് വിവരം വേണം|{topic} കുറിച്ച് എന്തെങ്കിലും പറയൂ|{topic} സംബന്ധിച്ച ഒരു അവലോകനം തരൂ|{topic} സംബന്ധിച്ച പൊതുവിവരം തരൂ'),
        'extra': words('{topic} ന്റെ അടിസ്ഥാന കാര്യങ്ങൾ പറയൂ|{topic} ന്റെ പശ്ചാത്തലം തരൂ|{topic} ന്റെ പിന്നാമ്പുറം വിശദീകരിക്കൂ|{topic} ന്റെ വ്യാഖ്യാനം തരൂ|{topic} ന്റെ ചുരുക്കപരിചയം തരൂ'),
        'raise': words('{product}യ്ക്ക് റിപെയർ ബുക്ക് ചെയ്യുക|{product}യ്ക്ക് സർവീസ് അഭ്യർത്ഥന രജിസ്റ്റർ ചെയ്യുക|{product}യ്ക്ക് ടെക്നീഷ്യനെ അയയ്ക്കുക|{product}യ്ക്ക് റിപെയർ ടിക്കറ്റ് സൃഷ്ടിക്കുക|{product}യ്ക്ക് സർവീസ് സമയം നിശ്ചയിക്കുക'),
        'amc': words('{product}യ്ക്ക് AMC പദ്ധതികൾ കാണിക്കുക|{product}യ്ക്ക് പരിപാലന പദ്ധതികൾ പറയുക|{product}യ്ക്ക് AMC വിവരങ്ങൾ പങ്കിടുക|{product}യ്ക്ക് AMC ഓപ്ഷനുകൾ താരതമ്യം ചെയ്യുക|{product}യ്ക്ക് പരിപാലന കവറേജ് വിശദീകരിക്കുക'),
        'discover': words('{product}യുടെ പുതിയ മോഡലുകൾ കാണിക്കുക|{product}യുടെ പുതിയ ഉൽപ്പന്നങ്ങൾ കാണിക്കുക|{product}യുടെ ഏറ്റവും പുതിയ ഓപ്ഷനുകൾ ശുപാർശ ചെയ്യുക|{product}യുടെ പുതിയ കാറ്റലോഗ് പങ്കിടുക|{product}യുടെ പുതിയ മോഡലുകൾ കണ്ടെത്താൻ സഹായിക്കുക'),
        'points': words('{product}യ്ക്ക് ലോയൽറ്റി പോയിന്റുകൾ പരിശോധിക്കുക|{product}യ്ക്ക് റിവാർഡ് പോയിന്റുകൾ കാണിക്കുക|{product}യുടെ ലോയൽറ്റി ബാലൻസ് പറയുക|{product}യുടെ പോയിന്റുകൾ കാണണം|{product}യ്ക്ക് ലഭ്യമായ പോയിന്റുകൾ കാണിക്കുക'),
        'register': words('എന്റെ {product} രജിസ്റ്റർ ചെയ്യുക|{product} എന്റെ അക്കൗണ്ടിൽ ചേർക്കുക|{product}യുടെ വാർന്റി രജിസ്ട്രേഷൻ പൂർത്തിയാക്കുക|{product} എന്റെ പ്രൊഫൈലുമായി ലിങ്ക് ചെയ്യുക|{product} രജിസ്ട്രേഷൻ നടത്തുക'),
        'jib': words('ഝ്രാക് ???|ബ്ലോം @@|കുവാർ 42|തുപ്പ് %%|ഗ്രാഫ് ???|ധ്രും ###|പ്ലാക് ??|ക്ലൂം 000|സ്രാപ് %%|വ്രാക് ??'),
        'noise': {'ഇന്ന്','നാളെ','ഇപ്പോൾ','ഇന്നലെ','വേഗം','മന്ദം','നല്ല','ചീത്ത','ഉത്തരം'}
    }
})

def dedupe_norm(text, language):
    tokens = normalize(text).split()
    return ' '.join(t for t in tokens if t not in SPECS[language]['noise'])

def gen_queries(language):
    s = SPECS[language]
    greet = [f'{g}, {a}' for g in s['greet'] for a in s['addrs']]
    device = [t.format(product=p) for t in s['device'] for p in s['products']]
    regular_out = [t.format(topic=x) for t in s['out'] for x in s['topics']] + [t.format(topic=x) for t, x in zip(s['extra'], s['topics'][:5])]
    service = {
        'raise_service_request': [t.format(product=p) for t in s['raise'] for p in s['products']],
        'explore_amc_plans': [t.format(product=p) for t in s['amc'] for p in s['products']],
        'discover_new_products': [t.format(product=p) for t in s['discover'] for p in s['products']],
        'check_loyalty_points': [t.format(product=p) for t in s['points'] for p in s['products']],
        'register_product': [t.format(product=p) for t in s['register'] for p in s['products']],
    }
    assert len(greet) == 375 and len(device) == 375 and len(regular_out) == 365
    for vals in service.values():
        assert len(vals) == 75
    return {
        ('greetings', language, None): [{'query': q} for q in greet],
        ('device_control', language, None): [{'query': q} for q in device],
        ('out_of_scope', language, None): [{'query': q} for q in regular_out],
        ('out_of_scope', language, 'jebrish_commands'): [{'query': q, 'sub_category': 'jebrish_commands'} for q in s['jib']],
        ('service_request', language, 'raise_service_request'): [{'query': q, 'sub_category': 'raise_service_request'} for q in service['raise_service_request']],
        ('service_request', language, 'explore_amc_plans'): [{'query': q, 'sub_category': 'explore_amc_plans'} for q in service['explore_amc_plans']],
        ('service_request', language, 'discover_new_products'): [{'query': q, 'sub_category': 'discover_new_products'} for q in service['discover_new_products']],
        ('service_request', language, 'check_loyalty_points'): [{'query': q, 'sub_category': 'check_loyalty_points'} for q in service['check_loyalty_points']],
        ('service_request', language, 'register_product'): [{'query': q, 'sub_category': 'register_product'} for q in service['register_product']],
    }

CANON = {}
QUERY_MAP = {}
for lang in LANGUAGES:
    buckets = gen_queries(lang)
    CANON.update(buckets)
    for (intent, _lang, subcat), rows in buckets.items():
        for row in rows:
            QUERY_MAP[(lang, normalize(row['query']))] = (intent, row.get('sub_category'))


def bucket_key(item):
    subcat = item.get('sub_category')
    if item['expected_response_type'] == 'service_request':
        return ('service_request', item['language'], subcat)
    if item['expected_response_type'] == 'out_of_scope' and subcat == 'jebrish_commands':
        return ('out_of_scope', item['language'], 'jebrish_commands')
    return (item['expected_response_type'], item['language'], None)


def classify(query, language):
    if any(mark in query for mark in BROKEN_MARKERS):
        return 'out_of_scope', 'jebrish_commands'
    return QUERY_MAP.get((language, normalize(query)), ('unknown', None))


def validate_source(data):
    dup_map = defaultdict(list)
    mismatches, invalid_sub, encoding = [], [], []
    for item in data:
        dup_map[(item['language'], dedupe_norm(item['query'], item['language']))].append(item['id'])
        pred_intent, pred_sub = classify(item['query'], item['language'])
        if pred_intent != 'unknown' and (pred_intent != item['expected_response_type'] or pred_sub != item.get('sub_category')):
            mismatches.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'expected': f"{item['expected_response_type']}:{item.get('sub_category')}", 'predicted': f'{pred_intent}:{pred_sub}'})
        if any(mark in item['query'] for mark in BROKEN_MARKERS):
            encoding.append({'id': item['id'], 'language': item['language'], 'query': item['query']})
        if item['expected_response_type'] == 'service_request':
            if item.get('sub_category') not in SERVICE_SUBCATEGORIES:
                invalid_sub.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'subcategory': item.get('sub_category')})
        elif item['expected_response_type'] == 'out_of_scope' and item.get('sub_category') == 'jebrish_commands':
            pass
        elif 'sub_category' in item:
            invalid_sub.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'subcategory': item.get('sub_category')})
    duplicates = [{'language': lang, 'normalized_query': norm, 'ids': ids} for (lang, norm), ids in dup_map.items() if norm and len(ids) > 1]
    return {'duplicates': duplicates, 'mismatches': mismatches, 'invalid_subcategories': invalid_sub, 'encoding_issues': encoding}


def build_corrected(source):
    counts = Counter(bucket_key(item) for item in source)
    for key, count in counts.items():
        if key not in CANON or len(CANON[key]) != count:
            raise ValueError(f'Bucket mismatch for {key}: {count} vs {len(CANON.get(key, []))}')
    index = defaultdict(int)
    seq = defaultdict(int)
    fixed = 0
    corrected = []
    for item in source:
        key = bucket_key(item)
        repl = CANON[key][index[key]]
        index[key] += 1
        new_item = {'language': item['language'], 'expected_response_type': item['expected_response_type'], 'query': repl['query'], 'is_boundary': bool(item.get('is_boundary', False))}
        if 'sub_category' in repl:
            new_item['sub_category'] = repl['sub_category']
        seq[(new_item['expected_response_type'], new_item['language'])] += 1
        new_item['id'] = f"{new_item['expected_response_type']}_{new_item['language']}_{seq[(new_item['expected_response_type'], new_item['language'])]}"
        original = {'id': item.get('id'), 'language': item['language'], 'expected_response_type': item['expected_response_type'], 'query': item['query'], 'is_boundary': bool(item.get('is_boundary', False))}
        if 'sub_category' in item:
            original['sub_category'] = item['sub_category']
        if original != new_item:
            fixed += 1
        corrected.append(new_item)
    return corrected, fixed


def validate_corrected(data):
    dup_map = defaultdict(list)
    mismatches, invalid_sub, encoding = [], [], []
    seq = defaultdict(int)
    for item in data:
        dup_map[(item['language'], normalize(item['query']))].append(item['id'])
        pred_intent, pred_sub = classify(item['query'], item['language'])
        if pred_intent != item['expected_response_type'] or pred_sub != item.get('sub_category'):
            mismatches.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'expected': f"{item['expected_response_type']}:{item.get('sub_category')}", 'predicted': f'{pred_intent}:{pred_sub}'})
        if any(mark in item['query'] for mark in BROKEN_MARKERS):
            encoding.append({'id': item['id'], 'language': item['language'], 'query': item['query']})
        if item['expected_response_type'] == 'service_request':
            if item.get('sub_category') not in SERVICE_SUBCATEGORIES:
                invalid_sub.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'subcategory': item.get('sub_category')})
        elif item['expected_response_type'] == 'out_of_scope' and item.get('sub_category') == 'jebrish_commands':
            pass
        elif 'sub_category' in item:
            invalid_sub.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'subcategory': item.get('sub_category')})
        seq[(item['expected_response_type'], item['language'])] += 1
        expected_id = f"{item['expected_response_type']}_{item['language']}_{seq[(item['expected_response_type'], item['language'])]}"
        if not ID_PATTERN.match(item['id']) or item['id'] != expected_id:
            mismatches.append({'id': item['id'], 'language': item['language'], 'query': item['query'], 'expected': expected_id, 'predicted': item['id']})
    duplicates = [{'language': lang, 'normalized_query': norm, 'ids': ids} for (lang, norm), ids in dup_map.items() if norm and len(ids) > 1]
    return {'duplicates': duplicates, 'mismatches': mismatches, 'invalid_subcategories': invalid_sub, 'encoding_issues': encoding}


def run(dataset_path, report_path):
    with open(dataset_path, 'r', encoding='utf-8') as f:
        source = json.load(f)
    source_issues = validate_source(source)
    corrected, fixed = build_corrected(source)
    corrected_issues = validate_corrected(corrected)
    report = {
        'summary': {
            'total_samples': len(corrected),
            'duplicates_found': len(corrected_issues['duplicates']),
            'intent_mismatches': len(corrected_issues['mismatches']),
            'fixed_samples': fixed,
            'encoding_issues': len(corrected_issues['encoding_issues']),
        },
        'issues': {
            'duplicates': source_issues['duplicates'][:50],
            'mismatches': source_issues['mismatches'][:50],
            'invalid_subcategories': source_issues['invalid_subcategories'][:50],
            'encoding_issues': source_issues['encoding_issues'][:50],
        },
        'corrected_dataset': corrected,
    }
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(corrected, f, indent=2, ensure_ascii=False)
        f.write('\n')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('===== FINAL REPORT =====')
    print(f"Total: {len(corrected)}")
    print(f"Duplicates: {len(corrected_issues['duplicates'])}")
    print(f"Mismatches: {len(corrected_issues['mismatches'])}")
    print(f"Invalid subcategories: {len(corrected_issues['invalid_subcategories'])}")
    print(f"Encoding issues: {len(corrected_issues['encoding_issues'])}")
    print(f"Fixed samples: {fixed}")


def main():
    parser = argparse.ArgumentParser(description='Validate and clean the multilingual dataset.')
    parser.add_argument('--dataset', default='final_dataset_balanced_12000.json')
    parser.add_argument('--report', default='dataset_report.json')
    args = parser.parse_args()
    run(args.dataset, args.report)


if __name__ == '__main__':
    main()
