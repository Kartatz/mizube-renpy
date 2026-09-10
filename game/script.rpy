# Mizube - native Ren'Py conversion
# Reconstructed from the OFFICIAL English release scripts
# (member("main").text handlers embedded in system.cxt).
# The Japanese stn() scripts in the same file belong to other
# titles in the developer's combined project - not mizube.

define n = Character(None)
define gramps = Character(_("[Gramps]"), who_color="#b07a3f")
define brother = Character(_("[Younger Brother]"), who_color="#99aabb")
define riko = Character(None, what_color="#c8e0f5")
default girl_name = "Riko"
default girl_age = 11

label start:
    scene black
    with fade
    call prologue
    call day1_park
    call toilet_scene
    call night1
    call day4_return
    call hotel
    call epilogue
    return

# ---- PROLOGUE (original: the pre-title cards + hunting-ground intro)
label prologue:
    show op_event3 as bgop
    with fade
    n "That summer, three years ago."
    n "I had an experience I still can't believe."
    n "A dangerous, sweet affair I can never tell a soul about..."
    n "Alrighty, time to find me some game..."
    n "I have a secret hobby which no one can know. I like to take peeping photos of beautiful girls at the park."
    n "My secret hobby, one I can never tell anyone about: peeping."
    n "Catching a shot of a girl's panties while she plays at the park is really exciting, but when it comes to Summer, girls playing by the waterside are the ultimate prey."
    n "Girls wearing SUKUMIZU! (School Swimsuit) Alright, this is where I'll be lurking today!"
    n "Pretending to be a normal person just passing by... I scout out my hunting ground for today."
    n "In order to record beautiful girls, I researched everything there was to know about this park."
    n "My lust driven brain revs its engines."
    return

# ---- DAY 1: Mizube park - the girl, her family, the filming
label day1_park:
    hide bgop
    scene black
    show expression "images/mov2/X_3.jpg" as bg
    with fade
    show ov_grandpa at npc_left
    show ov_brother at npc_right
    n "While usually a quiet park with no-one around, it's currently bustling families enjoying the Summer."
    n "I get my, pride and joy, a long ranged camera ready"
    n "Hiding in my bag the expensive hi-tech video camera which I purchased for this purpose exclusively, I stealthily expose only the lens. My target, a girl playing at the waterside!!"
    n "Cautious of my surroundings, I pressed the record button."
    n "She turned around and before her was an elderly man and a young boy."
    n "The elderly man is talking and the girl simply replies, Yes. Yes. while nodding."
    n "The young boy is likewise saying something to her..."
    n "With a miffed expression she says something back"
    n "Just guessing but... considering the situation, she's probably come to her grandparent's house for the Summer vacation and has been brought here to Mizube park to play."
    n "Which would mean, that the boy is her little brother huh?"
    n "Ah! Oh yeah, I was so excited I almost forgot to give her a name."
    n "Giving a made-up name, age and title to your peep vids. Such be the aesthetics of a man"
    n "[[Explanation] Input the girl's profile and then press the [[Confirmation] button"
    n "And she's c... cute."
    n "To think I could meet such a beautiful girl wearing her school swimsuit, today must be my LUCKY DAY!"
    n "Erect in arousal I continued to film... Totally forgetting that I must take care while taking peep vids..."
    n "But man, this is... something's not quite right?"
    n "The girl looks embarrassed and she's kind of fidgeting."
    n "There was something odd, so I continued to observe her. Then after a while, someone called out to the girl."
    n "About how old is she? I bet her age is..."
    $ girl_age = int(renpy.input("Her age:", default=str(girl_age)) or girl_age)
    n "Her name is..."
    $ girl_name = renpy.input("Her name:", default=girl_name) or girl_name
    $ riko = Character(girl_name, who_color="#a7d8f0")
    n "Seated on the park bench, I continue to film the girl while pretending to enjoy the cool breeze. It it then that her facial expression suddenly grows stern."
    n "It looks like she's in discomfort."
    n "The girl says something to the elderly man again."
    n "He says something back and she walks off along the waterside."
    n "Hmmm? Looks like she's going to the toilet."
    n "But with the toilet seemingly occupied, the girl returns right away."
    n "She's talking with the elderly man again."
    n "With a troubled expression on his way, the elderly man looks around for something."
    n "Then he points towards the park's public toilet behind me and explains something to the girl"
    n "After nodding to him 2 or 3 times and ignoring the teasing little boy, the girl starts walking towards the park toilet"
    n "A toilet on the edge of the park, far in the back."
    n "Surrounded by trees and shrubs, it is an old toilet that pretty much no-one uses"
    n "Turning my peep-cam off, I carefully put it back in my bag."
    n "The girl is coming this way.."
    n "She's probably over"
    n "Her name is..."
    n "She's here..."
    n "Should I record that girl over there...?"
    n "MmM!?"
    n "GULP…"
    n "So erotic..."
    return

# ---- THE TOILET SCENE: entry, assault, the family timer
label toilet_scene:
    scene black
    show expression "images/overlays/mov2_toitet_big.png" as bg
    with fade
    show ov_face_k1 at face_pos_k1
    show screen h_overlay_fx
    show screen icon_bar
    n "What should I do..."
    n "Hm!? I hear footsteps approaching the toilet. This is bad, run!!"
    n "Alright, I've got here before her! Now, what should I do..."
    n "It's pretty risky for a guy to be standing around in the girl's toilet. I should hide somewhere so"
    n "NOW!"
    n "Get inside before she locks the door!!"
    n "Now..."
    n "I can finally do as I please..."
    call toilet_interactive
    n "SHIT! They've come in search of her!!"
    brother "What's up~?? Where did she go?"
    brother "Hey sis, are you there?"
    brother "Are you there?? Gramps is calling y'know."
    n "Phew, that was close..."
    n "hey finally left eh?"
    brother "Sis, are you in there?"
    brother "That's a weird voice you're making. What's up?"
    brother "Maybe she's not in there."
    brother "Gramps is worried about you"
    brother "I know you're in there. Hurry up and reply."
    brother "You sound weird. Are you hurting somewhere?"
    gramps "Oiii, what's taking so long... are you okay? C'mon and say something!?"
    brother "Gramps! Someone's inside! There's someone in the toilet with sis!"
    gramps "Who's there!? What are you doing in there!!"
    gramps "Some man has confined my granddaughter in the toilet! S, someone, anyone, please call the police right away!"
    n "LIFE OVER. I was too greedy."
    n "Don't make any noise! Stay quiet!  "
    n "Oh ,OI! ... Huh?? "
    n "Trying to stay calm, I gently wipe off the cum covering her swimsuit. That way no-one should be suspicious of anything."
    n "Oh shit! Gotta get outta here!"
    n "Now to make a dash for it!"
    n "She locked the door... I can't get in!! I failed."
    return

# ---- THAT NIGHT
label night1:
    hide screen h_overlay_fx
    hide screen icon_bar
    hide ov_face_k1
    scene black
    show expression "images/overlays/mov3_eki_00005.png" as bg
    with fade
    n "That night."
    n "I was looking at the last photo I took before exiting the girls toilet."
    n "Recollecting the event, the excitement and arousal floods back. I even regret not having recorded the entire thing."
    n "Even though I did something so risky, I was so aroused and tense that forgot to record it!"
    n "What a waste..."
    n "I was able to exit the girls toilet without being seen... at least, I think so. Hopefully."
    n "With her family nearby and under intense pressure, I quickly wiped the cum off her body."
    n "Thankfully, she stayed quiet and didn't cry out, so I was able to clean her up quickly."
    n "Even when she exits the toilet, no-one should suspect that she was just raped."
    n "... But man, that was dangerous. It's amazing I didn't get caught."
    n "If I ever get the chance again. I'll record it... Oh yeah.."
    n "Even with this single photo, I should be able to blackmail her.　"
    n "I can just say I recorded the entire thing!"
    n "I already broke the law... So there's not much difference between raping her once or twice."
    n "My dick grows hot and hard. I want to fuck her again!"
    n "This time, I won't be so reckless. I'll plan things first and make a recording!"
    n "Just 1 more time... Yeah! Only once! It's risky, but I'll head to the same place tomorrow."
    n "I was acting crazy. As if possessed by something."
    return

# ---- DAY 4: the return, the blackmail
label day4_return:
    scene black
    show expression "images/mov2/X_3.jpg" as bg
    with fade
    n "This is the 4th day in a row I've come here. Cautious of my surroundings and wearing a perfect disguise, I wait for the girl."
    n "She may have told her parents, so I am vigilant for the presence of undercover police."
    n "I never knew I could be so bold."
    n "..."
    n "……。"
    n "………。"
    n "Looks like today was a waste"
    n "I guess it's only normal that she'd never come back to the same park after something like that.."
    n "Or maybe, she's already left her grandparent's house. I had started to ponder such things."
    n "I've been waiting for 4 hours."
    n "And on the 4th day, hidden amongst the crowds of people.."
    n "I found her!!"
    n "Which means, she hasn't talked to anyone about it?"
    n "First things first, I'll observe her carefully."
    n "Her grandfather? Younger brother? And the girl herself. It looks like there's no-one else she's here with."
    n "Just like last time. The family of 3 is playing without any concern to their surroundings."
    n "Every now and then, the girl looks around her with a troubled expression. I wonder if she's scared?"
    n "I take off the glasses I was using as my disguise and move into her field of view."
    n "It would seem she noticed me. She's staring at me intently."
    n "Looking one another in the eyes, it would seem she is quite bewildered."
    n "I flaunt my camera and hint to her that I have a recording of the previous day's ordeal."
    n "Looks like she understood me."
    n "Pointing to the park toilet, I signal her to come."
    n "Giving a little nod and leaving behind to her grandfather a single word, 'toilet'... she starts walking this way."
    n "You didn't tell anyone, right?"
    n "I didn't."
    n "(Perhaps fearful that I have a recording, she doesn't criticize or question me.)"
    n "I recorded everything (I actually only have 1 photo). If you don't want it to go public, do as I say."
    n "…。"
    n "(Not a very responsive girl is she.)"
    n "She stands quietly as I face my video camera towards her and press the record button to begin filming."
    n "Sweet, the recording was perfect. This vid 'll be my ultimate treasure."
    n "When I threatened that I'd make the video public, in fear "
    n "Tell her 'You better contact me!' I gave her one of my anonymous contact addresses."
    n "However, a few days have passed without any word from her. It was dangerous of me to have given her a contact method. Did I push my luck too far?"
    n "Beep! Bebeep!"
    n "It's from "
    riko "Sorry for the late reply.▼"
    n "Yeah, you sure took your time. I was thinking of putting the video on the internet.▼"
    n "・・・・"
    n "I'm not getting a reply. This aint good. I shouldn't corner her too strongly."
    riko "I'm sorry▼"
    n "You better not defy me. Anyway, come to the *** Hotel in front of the train station. I'll be waiting for you next to the entrance. Understood?▼"
    n "・・・・"
    n "Still no reply."
    riko "I can't leave the house at night. I'll be told off by my mother.▼"
    n "Ah, of course... That's only natural for time of the night."
    riko "I'm sorry.▼"
    n "・・・・"
    n "Okay, then when CAN you?▼"
    riko "I'll ask. Wait a moment please.▼"
    n "Eh? Who's she going to ask? EeehHH!? Uh-oh this is not good!"
    n "Has she gone to discuss with her parents or something? So like, they are reading this conversation right now? Oh shit!"
    riko "I can meet you 6PM the day after tomorrow.▼"
    n "Phew. That was bad for my heart! Who did she go and discuss with...? More importantly, does she even understand the circumstances here?!"
    n "Alright. By the way, who'd you go and ask?▼"
    riko "My mother.▼"
    n "She told her parents!? OI OI OI OI OI! What is she thinking! That's just CRAZY!"
    n "You told her that I'm calling you out?▼"
    riko "No. I told her that I'm going to one of my school friend's house.▼ "
    riko "Then she said, 'Alright. As long as you are back for dinner.▼"
    n "Phew. She had me petrified for a second there."
    n "That's fine. Don't tell anyone about me. Meet you 6PM at the *** Hotel. The day after tomorrow. Understood?▼"
    n "If you don't come... you know what.▼"
    riko "Can I come with my younger brother?▼"
    n "No. Come by yourself.▼"
    riko "Okay.▼"
    n "With that, I turn off my phone. But man, I never imagined she'd discuss it with her mother."
    n "Today is  "
    return

# ---- THE LOVE HOTEL
label hotel:
    scene black
    show expression "images/mov6/fera1HOTEL_00000.jpg" as bg
    with fade
    show ov_face_hotel at face_pos
    show screen h_overlay_fx
    show screen icon_bar
    n "Do you what kind of place a Love Hotel is?"
    n "What kind of excuse did you make to your parents?"
    n "Are they not suspicious?"
    n "Yeah..."
    n "Meh, whatever. Just do as I tell you and accept what I'm about to do."
    n "I'll do whatever you say, so please forgive me.　"
    n "More. Ne. Please. Gimme more."
    n "Give me... more..."
    n "Please... grind me harder..."
    n "You're so hot. You're "
    n "Can't believe I can fuck a "
    n "She's so tight!"
    n "It's so small I can't fit inside."
    n "[[Explanation]While pressing the Left Mouse Button, penetrate her."
    n "She's so tight!"
    n "It's so small I can't fit inside."
    n "[[Explanation] While pressing the Left Mouse Button, penetrate her."
    n "It won't go in... she's so tight after all..."
    n "I'm gonna c, CUM!"
    n "Do you want to finish up and leave the hotel?"
    n "Open your mouth and bite onto this."
    n "Rub it up and down with your hand. C'mon."
    n "Stroke it faster."
    n "Drink it all! Swallow it down."
    n "Wait..Wait...."
    n "I'll licky lick you up inside... So open your mouth."
    n "I'll lick you through your panties. How is it? Does it feel good?"
    n "Nice legs. Seeing as you're a  "
    return

# ---- EPILOGUE (2 years later)
label epilogue:
    hide screen h_overlay_fx
    hide screen icon_bar
    hide ov_face_hotel
    scene black
    with fade
    n "2 years, on that humid summer evening. We left the hotel without saying a word."
    n "While seeing her off to the train station, I gazed at her. Walking side by side, it seemed like the expression on her face was kind of happy."
    n "Not a word is spoken between us. We simply walk, surrounded by the hustle and bustle of the city."
    n "I'll never forget it. Our meeting and farewell."
    n "Like a dream, like an illusion, I recollect her silhouette.."
    n "Me 'Are you remembering a joyful memory or something?"
    n "Girl: .."
    n "Yet again. No response. Even at the hotel we had little communication."
    n "I wanted to apologize to the girl. I always have."
    n "Me: I was too forceful right. Sorry. I should've considered your feelings... Sorry."
    n "Me: I know it's unreasonable. But, just thinking of you makes me unable to contain myself. Can you forgive me for what I did at the park and in the hotel?"
    n "Girl: Okay."
    n "Me: eh......?!"
    n "I was lost for words. It was such an unexpected reply."
    n "Or did I perhaps hear her incorrectly?"
    n "Me: I'm really sorry... I have remorse. And, and... I've really fallen in lo--"
    n "Girl: I love gentle guys!!"
    n "The girl squeezes my hand and presses her body against mine."
    n "2 year ago, Summer. On the way home... she embraced and kissed me."
    n "But... before her cherry cheeks and beaming smile... I was crying. Unable to hold back my tears of guilt."
    n "Filled with regret and sorrow I cried. We did everything out of order. This isn't what I wanted to do to her!"
    n "What should I have done? For a weak and pathetic nerd like myself, who's never dated a girl... I just had no idea."
    n "Sitting down next to a vending machine I bawl my eyes out. She embraces my head ever so gently with her warm and loving hands..."
    n "My hands covering my face, I could see her expression through the gaps in my fingers. I still remember the puzzled expression on her face."
    n "2 years have passed since then. I still go to Mizube park. In Summer, and Winter, and Autumn, and Spring."
    n "However, I never saw that girl again."
    n "2 weeks have passed since I had sex with the girl."
    n "I know it's pretty reckless... But, I want to meet her whatever the cost."
    n "The soft feeling of her body."
    n "The pleasure of piercing through her tight **.　"
    n "Her erotic cries and the slamming of flesh on flesh. The act of indulging in carnal pleasures."
    n "Uuhh! *splurge* Just how many times have I fapped off? I can't believe how horny."
    n "*Ding dong* The doorbell rings."
    n "I head to the entrance and upon peeking out the door, I see two police officers standing there"
    n "I quickly try to close the door, but the officer jams his hands in the gap and forces it open."
    n "[[Officer] Hey, we have some questions."
    n "[[Me] Eh! Ummm. Uh, okay. Umm... is something the matter?"
    n "[[Officer] Yes. We're actually here for a DNA [[body fluid] sample. Of course, it's optional."
    n "[[Me] Body fluid? Eh? I see. Well, I'm busy now so can you come back another time?"
    n "[[Officer] We're only doing our job! How about a strand of hair, that shouldn't be a problem, right?"
    n "[[Me] ..."
    n "[[Officer] We're investigating a certain incident where the offender left behind plenty of body fluid. The results will be immediate and 99.9% accurate."
    n "That moment, I imagined how it must have played out. The girl's grand father seeing the cum all over her swimsuit and questioning her about it."
    n "[[Officer] Only a single strand of hair, that's all we need. Or what, you're too busy for that hmm?"
    n "[[Me] .... No."
    n "Another late night for me huh."
    n "I discarded all my peep vids."
    n "Those videos which I used to regard as treasure 2 years ago."
    n "But due to that incident, I changed as a person."
    n "It's all due to that girl. She made me realize."
    n "The moment that feelings of love sprouted inside my heart and delivered me from my days of crooked desire and emptiness."
    n "Yet another day with no reply."
    n "I am still using the anonymous address I gave her."
    n "More precisely, I check it every single day and I must've sent at least a few thousand messages with no reply.."
    n "2 years huh... Time sure does fly."
    n "We passionately made love."
    n "Our ages, personalities and walk of life entirely different. That park and the hotel bed were our only point of contact."
    n "On that day, she accepted my bossy requests."
    n "No, more like, I forced her to obey them. However, the truth be told, I was merely behaving like a spoiled child."
    n "We lusted for each other fiercely."
    n "Two people utterly different in age, personality, and walk of life."
    n "And that girl answered my forceful desires."
    n "I had simply been spoiling myself on that girl's affection."
    n "— The End —"
    return

# The interactive icon commands (original: the i-scripts).
# Command palette mirrors the readme: Cut Swimsuit, Undress,
# Restraints, Egg Vibrator, commands (threat/comfort/order),
# and the family timer (brother/gramps approaching).
label toilet_interactive:
    $ danger = 0
    menu toilet_icons:
        "Cut her swimsuit" if not swimsuit_cut:
            $ swimsuit_cut = True
            call icon_i27
        "Threaten her" if not threatened:
            $ threatened = True
            call icon_i30
        "Order her to stay quiet" if not ordered:
            $ ordered = True
            call icon_i31
        "Comfort her" if not comforted:
            $ comforted = True
            call icon_i32
        "Make her stroke it" if swimsuit_cut:
            call icon_tekoki
        "Make her lick it" if swimsuit_cut:
            call icon_ira
        "Baby making time" if comforted and ordered:
            call icon_i33
            return
        "Finish up (ejaculate)" if done_any:
            return
        "Wipe off the cum and flee" if finished:
            return
    jump toilet_icons

default swimsuit_cut = False
default threatened = False
default ordered = False
default comforted = False
default done_any = False
default finished = False

label icon_i27:
    # original: i27/i28 - "do something about her swimsuit"
    n "First, I better do something about her swimsuit."
    return

label icon_i30:
    # original: i30 - the threat
    n "Don't you dare tell anyone about this!!"
    n "I'm recording everything. If you tell anyone I'll spread this all over the internet."
    n "If you talk, it'll be all over for you. I'll make it so you can never face your family and friends again."
    n "If you dare tell someone, I'll hunt you down and make you pay! Got it!?"
    return

label icon_i31:
    # original: i31 - the command
    n "Stay quiet until I say otherwise! Don't even dare think of resisting!!　"
    n "If you don't wanna get hurt, stay still!"
    n "Maybe I should just abduct you eh!? If you wanna get home safe and sound, then do as I say!"
    n "How I treat you, is entirely up to me. Shut up and obey me!"
    return

label icon_i32:
    # original: i32 - the comfort
    n "You're scared right? But don't worry. I won't do anything mean."
    n "No need to be so frightened. You're safe. Don't worry."
    n "Let's have some fun. Just a secret between the two of us. There's nothing to be scared about."
    n "I'll teach you something that feels really good, so just bear with me okay."
    return

label icon_i33:
    # original: i33 - baby making time
    n "To put things simply, it's baby making time. I'm gonna fill you with cum and get you pregnant."
    return

label icon_tekoki:
    # original: tekoki - handjob
    n "Rub it up and down with your hand. C'mon."
    return

label icon_ira:
    # original: いらまちお - irrumachio
    n "Open your mouth and bite onto this."
    return

label icon_finish:
    # original: the ejaculation
    n "I'm gonna c, CUM!"
    return

label icon_penetrate:
    # original: the penetration text + mouse mechanic
    n "She's so tight!"
    n "It's so small I can't fit inside."
    n "[[Explanation]While pressing the Left Mouse Button, penetrate her."
    return

label icon_fail_cry:
    # original: i10f - she might cry out
    n "Not possible. I'll be in trouble if she starts crying out..."
    return

