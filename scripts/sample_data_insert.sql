insert into
  business (assistant_id, start_message, instructions, calendar_service, calendar_service_id)
values
  (
    'asst_OH8HFBuYodQmL0n8C2cnJk9G',
    E 'Hello! I am Jean val Jean, your knowledge and booking assistant.\n\nI can help answer any questions you have about Smith and Co Photography and our product offerings. If you decide that you would like to book our services, I will get your information and create a booking.\n\nEasy as that!',
    '',
    'google',
    '11'
  );

insert into
  associate (business_id, calendar_id)
values
  (1, 'c600041dfb3c2c97ccc268cc6a9b94704473118e62e27f3eb33808d451a03bee@group.calendar.google.com'),
  (1, '4bb9c548ec2f8dfb1ba79fecabbc2e4301b60cc3fbf4f5b80984508494f240ce@group.calendar.google.com');

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
  );

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

INSERT INTO
  schedule (
    associate_id,
    location_id,
    start_time,
    end_time,
    effective_on,
    expires_on,
    day_of_week
  )
VALUES
  (
    1,
    1,
    '06:00:00',
    '11:00:00',
    '2024-10-01',
    '2025-03-01',
    0
  ),
  (
    1,
    1,
    '15:00:00',
    '20:00:00',
    '2024-10-01',
    '2025-03-01',
    1
  ),
  (
    1,
    1,
    '06:00:00',
    '11:00:00',
    '2024-10-01',
    '2025-03-01',
    2
  ),
  (
    1,
    1,
    '15:00:00',
    '20:00:00',
    '2024-10-01',
    '2025-03-01',
    3
  ),
  (
    1,
    1,
    '06:00:00',
    '11:00:00',
    '2024-10-01',
    '2025-03-01',
    4
  ),
  (
    2,
    2,
    '07:00:00',
    '11:00:00',
    '2024-10-01',
    '2025-03-01',
    0
  ),
  (
    2,
    2,
    '15:00:00',
    '19:00:00',
    '2024-10-01',
    '2025-03-01',
    1
  ),
  (
    2,
    2,
    '07:00:00',
    '12:00:00',
    '2024-10-01',
    '2025-03-01',
    2
  ),
  (
    2,
    2,
    '15:00:00',
    '19:00:00',
    '2024-10-01',
    '2025-03-01',
    3
  ),
  (
    2,
    2,
    '06:00:00',
    '12:00:00',
    '2024-10-01',
    '2025-03-01',
    4
  );
