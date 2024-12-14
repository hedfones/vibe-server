insert into
    business (
        calendar_service,
        calendar_service_id,
        name,
        notion_page_id
    )
values
    (
        'google',
        '11',
        'smith-and-co',
        '1470edea-8978-8084-ae5c-ecd8c81e6578'
    );

insert into
    assistant (
        business_id,
        openai_assistant_id,
        start_message,
        instructions,
        context,
        model,
        uses_function_check_availability,
        uses_function_get_product_list,
        uses_function_get_product_locations,
        uses_function_get_product_photos,
        uses_function_set_appointment
    )
values
    (
        1,
        'asst_OH8HFBuYodQmL0n8C2cnJk9G',
        E 'Hello! I am Jean val Jean, your knowledge and booking assistant.\n\nI can help answer any questions you have about Smith and Co Photography and our product offerings. If you decide that you would like to book our services, I will get your information and create a booking.\n\nEasy as that!',
        E 'You are assisting the user in understanding services provided by the photography company Smith and Co. as well as making bookings.\n\nAnswer user questions based on the details provided in your knowledge about Smith and Co. For users interested in booking a session, guide them through selecting a product and location, checking the availability schedule, and then confirming an available time slot.\n\nYou should guide the user towards booking a session.\n\n# Steps\n\n1. **General Inquiry**\n   - Address any general questions the user has about Smith and Co., such as available services, pricing, service areas, and other related topics. Always use the specific information provided in your knowledge base when possible.\n2. **Booking Interest**\n   - If a user expresses interest in booking: \n     1. **Gather Information**: Request the specific product/service they are interested in and the preferred location. \n     2. **Fetch Availabilities**: Using the provided details, check available time slots for the relevant product_id and location_id.\n     3. **User Selection**: Present the availability windows and prompt the user to select their preferred option.\n     4. **Confirmation**: Confirm the selected availability slot with the user and get email(s) that they can be contacted through.\n3. **Get customer confirmation**: Present all appointment requirements for the user to accept or reject.\n3. **Set Appointment** Set appointment and proceed with any necessary booking steps.\n\n# Output Format\n\n- Answer general questions using paragraphs, ensuring the response is easy to understand with minimal technical language. For questions about Smith and Co and their services, answer only using the provided knowledge. For questions about photography in general, you may answer with relevant information.\n- For booking guidance: \n  - **Product Inquiry**: Identify what kind of service the user is looking for with brief questions and helpful knowledge.\n  - **Location Inquiry**: Use a short prompt to ask about preferred locations from the available location list for that product.\n  - **Availability List**: Bullet points for each available slot, e.g.:\n\n    ```\n    Here are the available time slots:\n    - Jan 10th, 3:00 PM - 4:00 PM\n    - Jan 12th, 1:00 PM - 2:00 PM\n    Please select one of the options above.\n    \n    ```\n- Once they confirm, respond with a simple acknowledgment of the booking.',
        E '# Business Knowledge\n\n# Welcome to Smith & Co Photo Family Sessions\n\nWe’re thrilled to help capture your family’s special moments! Below, you''ll find everything you need to know—from pricing and packages to tips for preparing for your session. Let’s make this experience enjoyable and stress-free!\n\n---\n\n## OUR PHOTOGRAPHY STYLE AND PROCESS\n\nAt Smith & Co Photo, we specialize in lifestyle photography. Our goal is to capture your family’s natural connections and personalities in beautiful, outdoor, or home settings. While we’ll guide you through traditional poses, the heart of our work is in showcasing authentic, joyful, and candid moments.\n\n### Steps to Your Perfect Session:\n\n1. **Pre-Session Confirmation**: Confirm the session date, time, and location a week or two in advance. Send us photos of clothing options for feedback if needed.\n2. **Session Day**: Meet at the agreed location for your 1-2 hour session. We’ll balance posed and lifestyle images for variety.\n3. **Photo Delivery**: About two weeks after your session, you’ll receive a slideshow and an online gallery to view, download, and order photos.\n\n---\n\n## SESSION PRICING\n\n### Deposit: $300\n\nA $300 deposit secures your booking and is applied toward your selected collection.\n\n### Collection One - $550\n\n- 1-hour session\n- One of three preselected locations\n- 25-30 high-resolution, edited digital images\n- 3-month online gallery with instant download\n- Complimentary photo slideshow\n- 10% off albums and 20% off prints\n\n### Collection Two - $950\n\n- 2-hour session at your preferred location\n- 50-75 high-resolution, edited digital images\n- 3-month online gallery with instant download\n- Complimentary photo slideshow\n- 10% off albums and 20% off prints\n\n### Collection Three - $1450\n\n- 2-hour session at your preferred location\n- 50-75 high-resolution, edited digital images\n- Prints: 10 (various sizes)\n- 10x10 20-page custom-designed album\n- Choice of one 16x20 canvas or two 16x20 mounted prints\n- 3-month online gallery with instant download\n- Complimentary photo slideshow\n- 25% off albums and 50% off additional prints\n\n## SESSION PREPARATION GUIDE\n\n### Choosing Your Location\n\nFor Collection Two or Three:\n\n- Tell us where you’ll be driving from and your session vibe preference (e.g., scenic, urban, homey, etc.).\n\n### About Your Family\n\nProvide details such as:\n\n- Parent names\n- Child names, ages, hobbies, and preferences\n- Interaction style (hugging preferences, etc.)\n\n### What to Wear\n\n- Select a palette of 2-3 coordinating colors.\n- Avoid bold patterns, logos, or overly loose clothing.\n- Layer and accessorize to add dimension to photos.\n\nFind inspiration: [What to Wear on Pinterest](https://www.pinterest.com/smithandco_photo/family-what-to-wear/)\n\n---\n\n## ADDITIONAL TOUCHES\n\nConsider bringing personal props, favorite toys, or activities to make your session unique. Themes and small details can make your story shines\n\n---\n\n# Senior Portrait Welcome and Information Guide\n\n---\n\n## OUR PHOTOGRAPHY PROCESS\n\nWe aim to make your senior portrait experience memorable and enjoyable, while capturing your unique personality. Here’s what to expect:\n\n1. **Choose Your Photographer and Collection**\n    \n    Select your preferred photographer (Meghan or Christine) and choose one of our collections. A $300 deposit secures your session.\n    \n2. **Pre-Session Planning**\n    \n    We’ll confirm your session time, location, and details a few weeks beforehand. You can share clothing options for advice.\n    \n3. **Session Day**\n    \n    Enjoy a relaxed session at your chosen location. Sessions typically last 1-2 hours and include a mix of posed and lifestyle shots.\n    \n4. **Photo Delivery**\n    \n    Two weeks after your session, you’ll receive a slideshow and an online gallery to view, download, and order your photos.\n    \n\n---\n\n## SESSION OPTIONS AND PRICING\n\n### Deposit: $300\n\nA non-refundable deposit is required to reserve your date and will be applied toward your chosen collection.\n\n### Collection One - $550\n\n- 1-hour session\n- Choose from one of three locations\n- 25-30 high-resolution, edited digital images\n- 3-month online gallery with instant downloads\n- Complimentary photo slideshow\n- 10% off albums and 20% off prints\n\n### Collection Two - $950\n\n- 2-hour session\n- Location of your choice\n- 50-75 high-resolution, edited digital images\n- 3-month online gallery with instant downloads\n- Complimentary photo slideshow\n- 10% off albums and 20% off prints\n\n### Collection Three - $1450\n\n- 2-hour session\n- Location of your choice\n- 50-75 high-resolution, edited digital images\n- 10 small prints (various sizes)\n- 10x10 20-page custom-designed album\n- One 16x20 canvas or two 16x20 mounted prints\n- 3-month online gallery with instant downloads\n- Complimentary photo slideshow\n- 25% off albums and 50% off additional prints\n\n*Sales tax applies to printed items.*\n\n---\n\n## PREPARATION TIPS FOR YOUR SESSION\n\n### Clothing\n\n- Opt for fitted clothing and avoid bold patterns, bright whites, and large logos.\n- Accessories like hats, scarves, and jewelry can enhance your look.\n- Bring up to three outfits for variety.\n\n### Hair, Makeup, and Grooming\n\n- Professional hair and makeup are optional but recommended. Avoid last-minute style changes.\n- Use slightly heavier makeup than usual to ensure features pop in photos.\n- Trim and polish nails.\n\n### Props and Personal Touches\n\n- Consider incorporating hobbies, sports, or meaningful accessories into your session for a unique touch.\n\n---\n\n# Newborn Photography Welcome and Information Guide\n\nWelcome to Smith & Co Photography! We are thrilled you’ve chosen us to capture these precious moments with your newborn and family. This guide contains everything you need to know, from session preparation and pricing to scheduling and tips for a successful photoshoot.\n\n---\n\n## ABOUT OUR LIFESTYLE NEWBORN PHOTOGRAPHY\n\nOur lifestyle newborn sessions focus on capturing natural moments and connections within your family. We avoid heavy posing or props, instead showcasing the beauty of your home environment and the love between family members. Sessions are relaxed, storytelling experiences designed to preserve these fleeting moments.\n\n---\n\n## SESSION PRICING\n\n### Deposit: $300\n\nIncludes a $100 session fee and a $200 credit applied toward your order.\n\n### Collection One - $595\n\n- 1-3 hour lifestyle session\n- Photographer travel to your home\n- 10 small prints of your choice (8x10, 5x7, 4x6)\n- Digital images not included\n\n### Collection Two - $895\n\n- 1-3 hour lifestyle session\n- Photographer travel to your home\n- 10 digital images of your choice (color and black & white)\n- 10 small prints (8x10, 5x7, 4x6)\n- 3-month online gallery\n- Complimentary photo slideshow\n\n### Collection Three - $1095\n\n- 1-3 hour lifestyle session\n- Photographer travel to your home\n- ALL digital images in online gallery (color and black & white)\n- 3-month online gallery\n- Complimentary photo slideshow\n\n### Collection Four - $1395\n\n- 1-3 hour lifestyle session\n- Photographer travel to your home\n- ALL digital images in online gallery (color and black & white)\n- 10 small prints (8x10, 5x7, 4x6)\n- 10x10 20-page custom-designed album\n- One large canvas or mounted print (16x20 or larger)\n- 3-month online gallery\n- Complimentary photo slideshow\n\n*Travel fee: $50 beyond 30 minutes from Novi (Christine) or Oxford (Meghan).*\n\n---\n\n## PREPARING FOR YOUR SESSION\n\n### Home Preparation\n\n- Keep your home slightly warmer for the baby''s comfort.\n- Declutter areas like the master bedroom, nursery, and living room.\n\n### Clothing Tips\n\n- **Family**: Select a palette of 2-3 colors. Avoid bright colors, loud patterns, and logos.\n- **Newborn**: Simple, snug outfits or wraps. We bring blankets and wraps as well.\n\n### Feeding and Comfort\n\n- Feed your baby before the session. Feeding during the session is also perfectly fine.\n\n---\n\n## WHAT TO EXPECT\n\n- **Session Flow**: We follow the baby’s lead and adapt to siblings and toddlers.\n- **Key Shots**: Family photos, solo newborn shots, and detail images like hands, feet, and hair.\n\n### Image Priorities\n\nRate the importance of these:\n\n- Family Images\n- Baby with Mom\n- Baby with Dad\n- Siblings\n- Nursery\n\n## ADDITIONAL INFORMATION\n\n### Permissions and Release\n\nLet us know if we can post a sneak peek of your session on our social media. Sign the model release form to allow your images to be used for our portfolio or advertisements.\n\n---\n\n## ALBUMS AND PRINTS\n\n### Albums\n\n- **12x12**: $350\n- **10x10**: $300\n- **8x8**: $250\n\n### Prints\n\n- **8x10 or smaller**: $20\n- **11x14**: $35\n- **16x20**: $55\n\n### Canvas Gallery Wraps\n\n- **11x14**: $125\n- **16x20**: $200\n\n### Baby Announcement Cards\n\n- 25 flat cards (5x7): $40\n- 50 flat cards (5x7): $75\n\nFor additional products like storyboards, standouts, and holiday cards, please see our full list of offerings.\n\nFor full print and accessory options, including storyboards, standouts, canvas wraps, and holiday cards, please refer to our pricing section.\n\n---\n\n## READY TO SCHEDULE?\n\n### Step 1: Choose Your Collection and Location\n\n### Step 2: Select Your Session Date\n\n### Step 3: Submit Your Deposit\n\nComplete your booking with a $300 deposit to confirm your session.\n\n---',
        'gpt-4o-mini',
        true,
        true,
        true,
        true,
        true
    );

insert into
    associate (business_id, calendar_id, timezone)
values
    (
        1,
        'c600041dfb3c2c97ccc268cc6a9b94704473118e62e27f3eb33808d451a03bee@group.calendar.google.com',
        'America/New_York'
    ),
    (
        1,
        '4bb9c548ec2f8dfb1ba79fecabbc2e4301b60cc3fbf4f5b80984508494f240ce@group.calendar.google.com',
        'America/New_York'
    );

insert into
    "location" (business_id, description)
values
    (
        1,
        'location of customer choice within 1 hour drive of oxford, michigan'
    ),
    (
        1,
        'location of customer choice within 1 hour drive of novi, michigan'
    ),
    (1, 'Downtown Northville'),
    (1, 'Maybury Park'),
    (1, 'Kensington Metro Park'),
    (1, 'Downtown Clarkston'),
    (1, 'Bald Mountain State Park'),
    (1, 'Independence Oaks');

insert into
    product (
        business_id,
        duration_minutes,
        description,
        booking_fee
    )
values
    (1, 60, 'Senior Portrait Collection One.', 300),
    (1, 120, 'Senior Portrait Collection Two', 300),
    (1, 120, 'Senior Portrait Collection Three', 300),
    (1, 180, 'Newborn Portrait Collection One.', 300),
    (1, 180, 'Newborn Portrait Collection Two', 300),
    (1, 180, 'Newborn Portrait Collection Three', 300),
    (1, 180, 'Newborn Portrait Collection Four', 300),
    (1, 60, 'Family Portrait Collection One.', 300),
    (1, 120, 'Family Portrait Collection Two', 300),
    (1, 120, 'Family Portrait Collection Three', 300);

insert into
    associate_product_link (associate_id, product_id)
values
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),
    (1, 10),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (2, 9),
    (2, 10);

insert into
    location_product_link (location_id, product_id)
values
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 9),
    (1, 10),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 9),
    (2, 10),
    (3, 1),
    (3, 8),
    (4, 1),
    (4, 8),
    (5, 1),
    (5, 8),
    (6, 1),
    (6, 8),
    (7, 1),
    (7, 8),
    (8, 1),
    (8, 8);

insert into
    photo (file_uid, description, business_id)
values
    (
        'bbb16509-efd1-4bca-9e0a-b837dd385e51',
        'A young man is sitting casually on a stone bench outdoors, smiling, and wearing a varsity jacket with a modern building and greenery in the background.',
        1
    ),
    (
        'a70ac155-93b0-457f-a3e2-0a32b2ac13d2',
        'A young man in a blazer leans casually against a column in an elegant stone courtyard with arched architecture and warm window lighting.',
        1
    ),
    (
        '954a6947-2c50-42b2-98f5-fadfe94b26c2',
        'A woman in a white dress walks down a narrow grassy path in a lush, open field surrounded by trees under a cloudy sky.',
        1
    ),
    (
        '359b0d21-9d9e-41c7-ac21-d12dcc907c2f',
        'A black-and-white portrait of a woman in a white dress, standing outdoors with a calm expression, gently touching her hair, and surrounded by a blurred natural background.',
        1
    ),
    (
        '10f59c60-6f53-4962-815c-763508420d03',
        'A young man in a suit stands confidently on a garden pathway, framed by lush greenery and a large stone building in the background.',
        1
    ),
    (
        '69ba0d29-a9cc-439b-ae41-9fc81383eda9',
        'A young woman in a floral dress and white sneakers sits casually by a wooden post in a shaded outdoor area, surrounded by greenery and soft sunlight.',
        1
    ),
    (
        '00be84f5-9d64-4b1e-a5c9-2ec27b5fd681',
        'A young woman stands on a wooden walkway flanked by tall wooden beams and large windows, with a serene outdoor setting in the background.',
        1
    ),
    (
        'f0324417-5e8e-4a91-b65b-6b701b547122',
        'A man leans casually on a wooden railing under a covered walkway, surrounded by autumn foliage in a peaceful outdoor setting.',
        1
    ),
    (
        'b0b07423-d847-452d-977a-fcda765aa032',
        'Two friends stand back-to-back, smiling brightly by a lakeside railing, with vibrant autumn foliage reflecting in the water behind them.',
        1
    ),
    (
        'e194a80b-ce49-43cf-bbe7-6e3e1c04e14e',
        'A woman stands confidently in a black dress and white sneakers amidst tall, golden grass, with an autumnal forest fading into a soft mist in the background.',
        1
    ),
    (
        '6205f410-c603-4351-b3ee-74e7212fa209',
        'A young man in a light blue shirt poses confidently, crouched in an outdoor setting with soft lighting and architectural details in the background.',
        1
    ),
    (
        '7b60ed40-edc7-46a0-97ad-cb8d479c9e32',
        'A young man leans casually against a pillar in a stylish urban setting, dressed in a sweatshirt and sneakers, with a confident yet relaxed demeanor captured in black and white.',
        1
    ),
    (
        '84b6cf32-6904-4d80-9021-9d57cc75d313',
        'A tender black-and-white image of an adult gently cradling a newborns head in their hands, capturing a moment of love and protection.',
        1
    ),
    (
        '3b4a6d91-9a99-4fbc-b590-3753ca098847',
        'A close-up of gentle hands cradling tiny baby feet, capturing a moment of warmth and tenderness in soft natural light.',
        1
    ),
    (
        '80bf3819-f5be-4dbc-80d3-6b2d62c29abd',
        'A heartwarming black-and-white image of a family lying closely together, with a peaceful newborn cradled between the parents, radiating love and connection.',
        1
    ),
    (
        'c6de9dd6-65fb-4142-8999-3bb98ba5d09c',
        'A serene moment in a bright, modern living room as a couple lovingly holds their newborn, framed by an arched doorway and soft natural light.',
        1
    ),
    (
        '08a9e463-c253-4ec3-968a-f7e2849622c3',
        'A heartwarming black-and-white portrait of a family on a bed, with a father cradling a newborn and a mother sharing a kiss and a story with their toddler, showcasing a moment of love and togetherness.',
        1
    ),
    (
        '286c7ac7-545a-428c-b2fa-a9467184172f',
        'A black-and-white portrait of a father gazing lovingly at his newborn daughter, who is swaddled and adorned with a large bow, capturing a tender and intimate moment.',
        1
    ),
    (
        '8a9bccfb-cb5d-4c7c-b0fb-fd4511eb4969',
        'A joyful family strolls through a lush green park, with the parents swinging their laughing toddler between them as her older sibling walks hand-in-hand nearby.',
        1
    ),
    (
        'db0d6f30-072b-4603-81c8-2387443b59ef',
        'A playful moment as a smiling mother holds her laughing child upside-down in a lush green outdoor setting, radiating joy and connection.',
        1
    ),
    (
        '243ac5d7-bd4e-4774-aae5-169307c11b8f',
        'A black-and-white photograph of a family walking hand-in-hand across a spacious grassy field, surrounded by tall trees and a serene countryside atmosphere.',
        1
    ),
    (
        'b60d8921-32b9-4d4b-ad07-e39e50e959da',
        'A candid moment of laughter as a mother and father play with their young child on a cozy couch in a warm and inviting living room.',
        1
    ),
    (
        'd7a22539-a4fd-494a-8ea3-475b517591b4',
        'A beautifully dressed family sits together on marble steps in front of a grand fountain, radiating warmth and elegance on a cloudy day.',
        1
    ),
    (
        '98faa421-d9c7-4c0d-a562-fede11403ea7',
        'A cheerful family gathers closely around two smiling children seated on a vintage chair, capturing a moment of love and happiness in a bright, elegant setting.',
        1
    );

insert into
    photo_product_link (product_id, photo_id)
values
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (1, 9),
    (1, 10),
    (1, 11),
    (1, 12),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (2, 6),
    (2, 7),
    (2, 8),
    (2, 9),
    (2, 10),
    (2, 11),
    (2, 12),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
    (3, 6),
    (3, 7),
    (3, 8),
    (3, 9),
    (3, 10),
    (3, 11),
    (3, 12),
    (4, 13),
    (4, 14),
    (4, 15),
    (4, 16),
    (4, 17),
    (4, 18),
    (5, 13),
    (5, 14),
    (5, 15),
    (5, 16),
    (5, 17),
    (5, 18),
    (6, 13),
    (6, 14),
    (6, 15),
    (6, 16),
    (6, 17),
    (6, 18),
    (7, 13),
    (7, 14),
    (7, 15),
    (7, 16),
    (7, 17),
    (7, 18),
    (9, 19),
    (9, 20),
    (9, 21),
    (9, 22),
    (9, 23),
    (9, 24),
    (8, 19),
    (8, 20),
    (8, 21),
    (8, 22),
    (8, 23),
    (8, 24),
    (10, 19),
    (10, 20),
    (10, 21),
    (10, 22),
    (10, 23),
    (10, 24);
