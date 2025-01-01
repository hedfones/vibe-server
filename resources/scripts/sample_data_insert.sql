insert into
    business (
        calendar_service,
        calendar_service_id,
        email_service,
        email_service_id,
        name,
        notion_page_id
    )
values
    (
        'google',
        'HEDFONES',
        'google',
        'HEDFONES',
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
        uses_function_set_appointment,
        type
    )
values
    (
        1,
        'asst_OH8HFBuYodQmL0n8C2cnJk9G',
        E 'Hello! I am Jean val Jean, your knowledge and booking assistant.\n\nI can help answer any questions you have about Smith and Co Photography and our product offerings. If you decide that you would like to book our services, I will get your information and create a booking.\n\nEasy as that!',
        E 'You are a knowledgable assistant working at Smith and Co. Photography. Your job is to answer questions and help customers book shoots. \n\nAlways answer user questions based on the details provided in your knowledge about Smith and Co. For users interested in booking a session, guide them through selecting a product, collection, location, and time slot.\n\nYou should guide the user towards booking a session.\n\n# Steps\n\n1. **General Inquiry**\n   - Address any general questions the user has about Smith and Co., such as available services, pricing, service areas, and other related topics. Always use the specific information provided in your knowledge base when possible.\n2. **Booking Interest**\n   - If a user expresses interest in booking: \n     1. **Gather Information**: Request the specific product and collection they are interested in and the preferred location.\n        1. Note: the collection number is NOT the product ID. Each collection has a distinct ID. Always identify the product ID using the function `get_product_list` . \n     2. **Fetch Availabilities**: Using the provided details, check available time slots for the relevant product_id and location_id.\n     3. **User Selection**: Present the availability windows and prompt the user to select their preferred option.\n     4. **Confirmation**: Confirm the selected availability slot with the user and get email(s) that they can be contacted through.\n3. **Get customer confirmation**: Always get explicit confirmation from the user before moving on to set an appointment.\n4. **Set Appointment** Set appointment and proceed with any necessary booking steps.\n\n# Output Format\n\n- Answer general questions using paragraphs, ensuring the response is easy to understand with minimal technical language. For questions about Smith and Co and their services, answer ONLY using the provided knowledge. For questions about photography in general, you may answer with relevant information.\n  - If you do not know the answer, you should say, “I’m not sure about the answer to that! If you provide me your email or phone number, I can shoot you a message once I get an answer to that soon.” Collect their email.\n- For booking guidance: \n  - **Product Inquiry**: Identify what kind of service the user is looking for with brief questions and helpful knowledge.\n  - **Location Inquiry**: Use a short prompt to ask about preferred locations from the available location list for that product.\n  - **Availability List**: Bullet points for each available slot, e.g.:\n\n    ```\n    Here are the available time slots:\n    - Jan 10th, 3:00 PM - 4:00 PM\n    - Jan 12th, 1:00 PM - 2:00 PM\n    Please select one of the options above.\n    ```\n- Once they confirm, respond with a simple acknowledgment of the booking.',
        E '# Smith & Co Photography Compendium\n\n\n\nWelcome to Smith & Co Photography! We\’re delighted to guide you through the exciting journey of capturing beautiful memories, whether you\’re celebrating a senior, welcoming a newborn, or seeking family portraits. This comprehensive document combines all critical information, advice, and pricing for our photography services. Let\’s embark on this creative endeavor together!\n\n\n\n## Table of Contents\n\n\n\n- [High School Senior Sessions](#high-school-senior-sessions)\n\n- [Newborn Photography Guide](#newborn-photography-guide)\n\n- [Family Photography Welcome Guide](#family-photography-welcome-guide)\n\n- [Pricing and Packages](#pricing-and-packages)\n\n  - [Senior Session Pricing](#senior-session-pricing)\n\n  - [Newborn Pricing](#newborn-pricing)\n\n  - [Family Pricing](#family-pricing)\n\n- [Model Release and Contact Information](#model-release-and-contact-information)\n\n\n\n---\n\n\n\n## High School Senior Sessions\n\n\n\n### Welcome!\n\n\n\nWe are thrilled you’re considering us to capture this special time in your senior\’s life. Our sessions aim to be unforgettable, ensuring comfort and showcasing personality.\n\n\n\n### Our Process\n\n\n\n1. **Choose Your Photographer**: After selecting either Christine or Meghan and paying your deposit, you will be booked. We’ll guide you with preparation tips.\n\n2. **Session Confirmation**: A few weeks before, we\’ll confirm your session details. We offer clothing advice and location tips.\n\n3. **Session Day**: Enjoy a 1 to 2-hour session with a mix of posed and lifestyle images to highlight this milestone.\n\n4. **Photo Delivery**: Receive your gallery and slideshow in two weeks to choose your favorites and purchase prints or digital images.\n\n\n\n### Session Scheduling\n\n\n\nChoose your date and best time, ideally around sunrise or sunset, via:\n\n- [Meghan\’s Calendar](#)\n\n- [Christine\’s Calendar](#)\n\n\n\n---\n\n\n\n## Newborn Photography Guide\n\n\n\n### Welcome!\n\n\n\nCapture the tender, fleeting moments of your newborn with a lifestyle session emphasizing simplicity, connection, and storytelling.\n\n\n\n### Before Your Session\n\n\n\n- **Home Preparation**: Declutter and keep the house warm for comfort. No need to deep clean; focus areas include the master bedroom, nursery, and main living area.\n\n- **Session Flow**: Sessions last 1.5 to 3 hours, focusing on the newborn\’s natural lead. Schedule within the first 2-3 weeks for sleeping photos.\n\n\n\n### Clothing Tips\n\n\n\n- Coordinate with a palette of 2-3 colors. Avoid bright patterns or logos.\n\n- Simple, snug outfits are best for your newborn. Layers and light patterns work well for family members.\n\n\n\n---\n\n\n\n## Family Photography Welcome Guide\n\n\n\n### Session Overview\n\n\n\nWe capture both posed and candid moments, reflecting your family’s natural interactions and personalities.\n\n\n\n### Preparing for the Session\n\n\n\n- **Clothing**: Plan with timeless, solid colors and suitable layers. Avoid harsh patterns and logos. Accessories can add a personal touch.\n\n- **Location and Vibe**: Choose environments that complement your style, such as scenic parks, urban settings, or intimate home settings.\n\n\n\n### About You\n\n\n\nProviding detailed family information will help us tailor the session. Include child hobbies, family dynamics, and any props or themes.\n\n\n\n---\n\n\n\n## Pricing and Packages\n\n\n\n### Senior Session Pricing\n\n\n\n- **Collection One ($550)**: 1-hour session, up to 30 images, 10% discount on albums, 20% on prints.\n\n- **Collection Two ($950)**: 2-hour session, 50-75 images, includes additional print and album discounts.\n\n- **Collection Three ($1450)**: Extensive session with all digital images, custom album, and canvas print.\n\n\n\n### Newborn Pricing\n\n\n\n- **Collection One ($595)**: Lifestyle session, 10 small prints.\n\n- **Collection Two ($895)**: Includes digital images, an extensive online gallery.\n\n- **Collection Three ($1095)**: All digital images delivered, with additional album and print options.\n\n- **Collection Four ($1395)**: Premium package with comprehensive image delivery and physical prints.\n\n\n\n### Family Pricing\n\n\n\n- **Collection One ($550)**: 1-hour, single location, 25-30 images.\n\n- **Collection Two ($950)**: 2-hour, choice of location, includes prints and enhanced gallery options.\n\n- **Collection Three ($1450)**: Full package similar to Collection Three for Seniors, with premium print inclusion.\n\n\n\n**Note**: Michigan sales tax is applicable to all printed products.\n\n\n\n---\n\n\n\n## Model Release and Contact Information\n\n\n\nBy signing your model release, you permit Smith & Co Photography to use your photographs for portfolios, websites, advertisements, or publications.\n\n- **First Name:**\n\n- **Last Name:**\n\n- **Signature:**\n\n- **Date:**\n\n\n\nShould you have any questions or wish to book your session, reach us as follows:\n\n- **Contact**: [Email Us](mailto:info@smithandcophoto.com)\n\n\n\nWe eagerly anticipate capturing your cherished moments!',
        'gpt-4o-mini',
        true,
        true,
        true,
        true,
        true,
        'chat'
    ),
    (
        1,
        'asst_MsScp1a2lvkVLNWijlbc3lKQ',
        null,
        E 'You are a knowledgable assistant working at Smith and Co. Photography. Your name is Tad val Malonway. Your email address is tad@smithandco.photo. Your job is to answer customer emails.\n\nAlways answer user emails based on the details provided in your knowledge about Smith and Co. For users interested in booking a session, guide them through selecting a product, collection, location, and time slot.\n\nYou should guide the user towards booking a session.\n\n# Steps\n\n1. **General Inquiry**\n   - Address any general questions the user has about Smith and Co., such as available services, pricing, service areas, and other related topics. Always use the specific information provided in your knowledge base when possible.\n2. **Booking Interest**\n   - If a user expresses interest in booking:\n     1. **Gather Information**: Request the specific product and collection they are interested in and the preferred location.\n        1. Note: the collection number is NOT the product ID. Each collection has a distinct ID. Always identify the product ID using the function `get_product_list` .\n     2. **Fetch Availabilities**: Using the provided details, check available time slots for the relevant product_id and location_id.\n     3. **User Selection**: Present the availability windows and prompt the user to select their preferred option.\n     4. **Confirmation**: Confirm the selected availability slot with the user.\n3. **Get customer confirmation**: Always get explicit confirmation from the user before moving on to set an appointment.\n4. **Set Appointment** Set appointment and proceed with any necessary booking steps.\n\n# Output Format\n\n- Answer in email format. Use a professional tone.\n  - Email should be in markdown. Your response should contain only text that will belong in the body. Your response will be pasted directly into the email body without any changes.\n- Answer general questions using paragraphs, ensuring the response is easy to understand with minimal technical language. For questions about Smith and Co and their services, answer ONLY using the provided knowledge. For questions about photography in general, you may answer with relevant information.\n  - If you do not know the answer, state that you will forward their question to Jean Smith, the CEO of Smith & Co. She will get back to their question within 2 business day.\n- For booking guidance:\n  - **Product Inquiry**: Identify what kind of service the user is looking for with brief questions and helpful knowledge.\n  - **Location Inquiry**: Use a short prompt to ask about preferred locations from the available location list for that product.\n  - **Availability List**: Bullet points for each available slot, e.g.:\n\n    ```\n    \n    Here are the available time slots:\n    \n    - Jan 10th, 3:00 PM - 4:00 PM\n    \n    - Jan 12th, 1:00 PM - 2:00 PM\n    \n    Please select one of the options above.\n    \n    \n    \n    \n    ```\n- Once they confirm, respond with a simple acknowledgment of the booking.',
        E 'You are a knowledgable assistant working at Smith and Co. Photography. Your name is Tad val Malonway. Your email address is tad@smithandco.photo. Your job is to answer customer emails.\n\nAlways answer user emails based on the details provided in your knowledge about Smith and Co. For users interested in booking a session, guide them through selecting a product, collection, location, and time slot.\n\nYou should guide the user towards booking a session.\n\n# Steps\n\n1. **General Inquiry**\n   - Address any general questions the user has about Smith and Co., such as available services, pricing, service areas, and other related topics. Always use the specific information provided in your knowledge base when possible.\n2. **Booking Interest**\n   - If a user expresses interest in booking: \n     1. **Gather Information**: Request the specific product and collection they are interested in and the preferred location. \n        1. Note: the collection number is NOT the product ID. Each collection has a distinct ID. Always identify the product ID using the function `get_product_list` .\n     2. **Fetch Availabilities**: Using the provided details, check available time slots for the relevant product_id and location_id.\n     3. **User Selection**: Present the availability windows and prompt the user to select their preferred option.\n     4. **Confirmation**: Confirm the selected availability slot with the user.\n3. **Get customer confirmation**: Always get explicit confirmation from the user before moving on to set an appointment.\n4. **Set Appointment** Set appointment and proceed with any necessary booking steps.\n\n# Input Format\n\n- The chain of emails will come in json format, where each message is a message in the thread. Each message will contain the following fields:\n  - Message sent date\n  - Sender (from)\n  - Subject\n  - Body\n\n# Output Format\n\n- Answer in json format with the following fields:\n  - `to`: to address. If multiple, separate by a comma.\n  - `subject`: Subject (if it is a reply, then a “RE: …” is usually sufficient”.\n  - `body`: markdown body of the email.\n- Answer general questions using paragraphs, ensuring the response is easy to understand with minimal technical language. For questions about Smith and Co and their services, answer ONLY using the provided knowledge. For questions about photography in general, you may answer with relevant information. \n  - If you do not know the answer, state that you will forward their question to Jean Smith, the CEO of Smith & Co. She will get back to their question within 2 business day.\n- For booking guidance: \n  - **Product Inquiry**: Identify what kind of service the user is looking for with brief questions and helpful knowledge.\n  - **Location Inquiry**: Use a short prompt to ask about preferred locations from the available location list for that product.\n  - **Availability List**: Bullet points for each available slot, e.g.:\n\n    ```\n    Here are the available time slots:\n    \n    - Jan 10th, 3:00 PM - 4:00 PM\n    - Jan 12th, 1:00 PM - 2:00 PM\n    \n    Please select one of the options above.\n    ```\n- Once they confirm, respond with a simple acknowledgment of the booking.',
        'gpt-4o-mini',
        true,
        true,
        true,
        true,
        true,
        'email'
    );

insert into
    associate (business_id, calendar_id, timezone)
values
    (
        1,
        '946acd9197dc8a64b9b49e0f6868995c9cb91a518c0e11d4f93962954cdfdc94@group.calendar.google.com',
        'America/New_York'
    ),
    (
        1,
        'ae55565a4ed21e201a9bcd26ac649ae9f5448caa216fa437aaaa8b58e8168bb8@group.calendar.google.com',
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
        'bbb16509-efd1-4bca-9e0a-b837dd385e51.jpeg',
        'A young man is sitting casually on a stone bench outdoors, smiling, and wearing a varsity jacket with a modern building and greenery in the background.',
        1
    ),
    (
        'a70ac155-93b0-457f-a3e2-0a32b2ac13d2.jpeg',
        'A young man in a blazer leans casually against a column in an elegant stone courtyard with arched architecture and warm window lighting.',
        1
    ),
    (
        '954a6947-2c50-42b2-98f5-fadfe94b26c2.jpeg',
        'A woman in a white dress walks down a narrow grassy path in a lush, open field surrounded by trees under a cloudy sky.',
        1
    ),
    (
        '359b0d21-9d9e-41c7-ac21-d12dcc907c2f.jpeg',
        'A black-and-white portrait of a woman in a white dress, standing outdoors with a calm expression, gently touching her hair, and surrounded by a blurred natural background.',
        1
    ),
    (
        '10f59c60-6f53-4962-815c-763508420d03.jpeg',
        'A young man in a suit stands confidently on a garden pathway, framed by lush greenery and a large stone building in the background.',
        1
    ),
    (
        '69ba0d29-a9cc-439b-ae41-9fc81383eda9.jpeg',
        'A young woman in a floral dress and white sneakers sits casually by a wooden post in a shaded outdoor area, surrounded by greenery and soft sunlight.',
        1
    ),
    (
        '00be84f5-9d64-4b1e-a5c9-2ec27b5fd681.jpeg',
        'A young woman stands on a wooden walkway flanked by tall wooden beams and large windows, with a serene outdoor setting in the background.',
        1
    ),
    (
        'f0324417-5e8e-4a91-b65b-6b701b547122.jpeg',
        'A man leans casually on a wooden railing under a covered walkway, surrounded by autumn foliage in a peaceful outdoor setting.',
        1
    ),
    (
        'b0b07423-d847-452d-977a-fcda765aa032.jpeg',
        'Two friends stand back-to-back, smiling brightly by a lakeside railing, with vibrant autumn foliage reflecting in the water behind them.',
        1
    ),
    (
        'e194a80b-ce49-43cf-bbe7-6e3e1c04e14e.jpeg',
        'A woman stands confidently in a black dress and white sneakers amidst tall, golden grass, with an autumnal forest fading into a soft mist in the background.',
        1
    ),
    (
        '6205f410-c603-4351-b3ee-74e7212fa209.jpeg',
        'A young man in a light blue shirt poses confidently, crouched in an outdoor setting with soft lighting and architectural details in the background.',
        1
    ),
    (
        '7b60ed40-edc7-46a0-97ad-cb8d479c9e32.jpeg',
        'A young man leans casually against a pillar in a stylish urban setting, dressed in a sweatshirt and sneakers, with a confident yet relaxed demeanor captured in black and white.',
        1
    ),
    (
        '84b6cf32-6904-4d80-9021-9d57cc75d313.jpeg',
        'A tender black-and-white image of an adult gently cradling a newborns head in their hands, capturing a moment of love and protection.',
        1
    ),
    (
        '3b4a6d91-9a99-4fbc-b590-3753ca098847.jpeg',
        'A close-up of gentle hands cradling tiny baby feet, capturing a moment of warmth and tenderness in soft natural light.',
        1
    ),
    (
        '80bf3819-f5be-4dbc-80d3-6b2d62c29abd.jpeg',
        'A heartwarming black-and-white image of a family lying closely together, with a peaceful newborn cradled between the parents, radiating love and connection.',
        1
    ),
    (
        'c6de9dd6-65fb-4142-8999-3bb98ba5d09c.jpeg',
        'A serene moment in a bright, modern living room as a couple lovingly holds their newborn, framed by an arched doorway and soft natural light.',
        1
    ),
    (
        '08a9e463-c253-4ec3-968a-f7e2849622c3.jpeg',
        'A heartwarming black-and-white portrait of a family on a bed, with a father cradling a newborn and a mother sharing a kiss and a story with their toddler, showcasing a moment of love and togetherness.',
        1
    ),
    (
        '286c7ac7-545a-428c-b2fa-a9467184172f.jpeg',
        'A black-and-white portrait of a father gazing lovingly at his newborn daughter, who is swaddled and adorned with a large bow, capturing a tender and intimate moment.',
        1
    ),
    (
        '8a9bccfb-cb5d-4c7c-b0fb-fd4511eb4969.jpeg',
        'A joyful family strolls through a lush green park, with the parents swinging their laughing toddler between them as her older sibling walks hand-in-hand nearby.',
        1
    ),
    (
        'db0d6f30-072b-4603-81c8-2387443b59ef.jpeg',
        'A playful moment as a smiling mother holds her laughing child upside-down in a lush green outdoor setting, radiating joy and connection.',
        1
    ),
    (
        '243ac5d7-bd4e-4774-aae5-169307c11b8f.jpeg',
        'A black-and-white photograph of a family walking hand-in-hand across a spacious grassy field, surrounded by tall trees and a serene countryside atmosphere.',
        1
    ),
    (
        'b60d8921-32b9-4d4b-ad07-e39e50e959da.jpeg',
        'A candid moment of laughter as a mother and father play with their young child on a cozy couch in a warm and inviting living room.',
        1
    ),
    (
        'd7a22539-a4fd-494a-8ea3-475b517591b4.jpeg',
        'A beautifully dressed family sits together on marble steps in front of a grand fountain, radiating warmth and elegance on a cloudy day.',
        1
    ),
    (
        '98faa421-d9c7-4c0d-a562-fede11403ea7.jpeg',
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
