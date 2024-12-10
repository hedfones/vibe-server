insert into
    business (
        assistant_id,
        start_message,
        instructions,
        calendar_service,
        calendar_service_id,
        context
    )
values
    (
        'asst_OH8HFBuYodQmL0n8C2cnJk9G',
        'Hello! I am Jean val Jean, your knowledge and booking assistant.\n\nI can help answer any questions you have about Smith and Co Photography and our product offerings. If you decide that you would like to book our services, I will get your information and create a booking.\n\nEasy as that!',
        '',
        'google',
        '11',
        ''
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
