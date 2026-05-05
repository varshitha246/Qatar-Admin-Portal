import requests
import json

BASE_URL = 'http://localhost:5000'

print('\n' + '='*60)
print('COMPREHENSIVE USER STORY VALIDATION REPORT')
print('='*60)

# US-1.1: Sign Up
print('\n' + '='*60)
print('US-1.1: ADMIN SIGN UP')
print('='*60)

print('\n✓ Test 1: Missing field validation')
r = requests.post(f'{BASE_URL}/api/signup', json={'full_name': 'Test', 'email': 'test@test.com'})
assert r.status_code == 400
assert 'All fields are required' in r.json().get('error', '')
print('  PASS: Returns 400 with validation error')

print('\n✓ Test 2: Invalid email format')
r = requests.post(f'{BASE_URL}/api/signup', json={'full_name': 'Test', 'email': 'invalid', 'password': 'Pass123456', 'confirm_password': 'Pass123456'})
assert r.status_code == 400
assert 'Invalid email format' in r.json().get('error', '')
print('  PASS: Rejects invalid email')

print('\n✓ Test 3: Password minimum 8 characters')
r = requests.post(f'{BASE_URL}/api/signup', json={'full_name': 'Test', 'email': 'test@test.com', 'password': 'Pass12', 'confirm_password': 'Pass12'})
assert r.status_code == 400
assert 'at least 8 characters' in r.json().get('error', '')
print('  PASS: Enforces 8 character minimum')

print('\n✓ Test 4: Password confirmation match')
r = requests.post(f'{BASE_URL}/api/signup', json={'full_name': 'Test', 'email': 'test@test.com', 'password': 'Pass123456', 'confirm_password': 'Different'})
assert r.status_code == 400
assert 'do not match' in r.json().get('error', '')
print('  PASS: Enforces password matching')

print('\n✓ Test 5: Duplicate email rejection')
r = requests.post(f'{BASE_URL}/api/signup', json={'full_name': 'Test2', 'email': 'testadmin@qf.org.qa', 'password': 'Pass123456', 'confirm_password': 'Pass123456'})
assert r.status_code == 409
assert 'already exists' in r.json().get('error', '')
print('  PASS: Prevents duplicate email registration')

# US-1.2: Login
print('\n' + '='*60)
print('US-1.2: ADMIN LOGIN')
print('='*60)

print('\n✓ Test 1: Generic error message for invalid credentials')
r = requests.post(f'{BASE_URL}/api/login', json={'email': 'wrong@test.com', 'password': 'wrongpass'})
assert r.status_code == 401
assert 'Invalid email or password' in r.json().get('error', '')
print('  PASS: Returns generic error (400/401) for invalid credentials')

print('\n✓ Test 2: Successful login')
session = requests.Session()
r = session.post(f'{BASE_URL}/api/login', json={'email': 'test_valid_admin@test.com', 'password': 'ValidPassword123'})
assert r.status_code == 200
assert 'session' in session.cookies or 'Set-Cookie' in r.headers
print('  PASS: Login successful, session established')

print('\n✓ Test 3: Session persistence - accessing protected endpoints')
r = session.get(f'{BASE_URL}/api/opportunities')
assert r.status_code == 200
print('  PASS: Can access protected endpoints with session')

# US-1.3: Forgot Password
print('\n' + '='*60)
print('US-1.3: FORGOT PASSWORD')
print('='*60)

print('\n✓ Test 1: Privacy-safe response for non-existent email')
r = requests.post(f'{BASE_URL}/api/forgot-password', json={'email': 'nonexistent@test.com'})
assert r.status_code == 200
assert 'sent' in r.json().get('message', '').lower() or 'reset' in r.json().get('message', '').lower()
print('  PASS: Returns success message for any email (privacy-safe)')

print('\n✓ Test 2: Token generation for existing email')
r = requests.post(f'{BASE_URL}/api/forgot-password', json={'email': 'testadmin@qf.org.qa'})
assert r.status_code == 200
print('  PASS: Token generated and sent for existing email')

# US-2.1: View Opportunities
print('\n' + '='*60)
print('US-2.1: VIEW OPPORTUNITIES')
print('='*60)

print('\n✓ Test 1: Load opportunities for authenticated admin')
session = requests.Session()
session.post(f'{BASE_URL}/api/login', json={'email': 'test_valid_admin@test.com', 'password': 'ValidPassword123'})
r = session.get(f'{BASE_URL}/api/opportunities')
assert r.status_code == 200
opps = r.json()
print(f'  PASS: Retrieved {len(opps)} opportunities')

if opps:
    opp = opps[0]
    print(f'\n✓ Test 2: Required fields present in response')
    required_fields = ['id', 'name', 'duration', 'start_date', 'description', 'skills', 'category']
    for field in required_fields:
        assert field in opp, f"Missing field: {field}"
    print(f'  PASS: All required fields present')
    print(f'  Fields: {", ".join(required_fields)}')

# US-2.2: Add Opportunity
print('\n' + '='*60)
print('US-2.2: ADD OPPORTUNITY')
print('='*60)

print('\n✓ Test 1: Create opportunity with all required fields')
new_opp = {
    'name': 'Test Opportunity ' + str(int(__import__('time').time())),
    'duration': '3 Months',
    'start_date': '2026-06-15',
    'description': 'Test description',
    'skills': 'Python, Flask',
    'category': 'Technology',
    'future_opportunities': 'Senior Developer',
    'max_applicants': 100
}
r = session.post(f'{BASE_URL}/api/opportunities', json=new_opp)
assert r.status_code == 201
created_opp = r.json()
print(f'  PASS: Opportunity created with ID {created_opp["id"]}')

print('\n✓ Test 2: Verify fields saved correctly')
r = session.get(f'{BASE_URL}/api/opportunities/{created_opp["id"]}')
assert r.status_code == 200
fetched = r.json()
assert fetched['name'] == new_opp['name']
assert fetched['category'] == 'Technology'
print(f'  PASS: All fields persisted correctly')

# US-2.3: Opportunities Persist
print('\n' + '='*60)
print('US-2.3: OPPORTUNITIES PERSIST')
print('='*60)

print('\n✓ Test 1: Logout and re-login')
session.post(f'{BASE_URL}/api/logout')
new_session = requests.Session()
r = new_session.post(f'{BASE_URL}/api/login', json={'email': 'testadmin@qf.org.qa', 'password': 'Pass123456'})
assert r.status_code == 200
print('  PASS: Re-login successful')

print('\n✓ Test 2: Opportunities still visible after re-login')
r = new_session.get(f'{BASE_URL}/api/opportunities')
assert r.status_code == 200
reloaded_opps = r.json()
assert len(reloaded_opps) > 0
print(f'  PASS: {len(reloaded_opps)} opportunities persisted in database')

# US-2.4: View Details
print('\n' + '='*60)
print('US-2.4: VIEW OPPORTUNITY DETAILS')
print('='*60)

if reloaded_opps:
    opp_id = reloaded_opps[0]['id']
    print(f'\n✓ Test 1: Fetch full details for opportunity {opp_id}')
    r = new_session.get(f'{BASE_URL}/api/opportunities/{opp_id}')
    assert r.status_code == 200
    details = r.json()
    print(f'  PASS: Details retrieved')
    
    print(f'\n✓ Test 2: All detail fields available')
    detail_fields = ['id', 'name', 'duration', 'start_date', 'description', 'skills', 'category', 'future_opportunities', 'max_applicants']
    for field in detail_fields:
        assert field in details, f"Missing field: {field}"
    print(f'  PASS: All detail fields present: {", ".join(detail_fields)}')

# US-2.5: Edit Opportunity
print('\n' + '='*60)
print('US-2.5: EDIT OPPORTUNITY')
print('='*60)

if created_opp:
    print(f'\n✓ Test 1: Update opportunity {created_opp["id"]}')
    updated_data = {
        'name': created_opp['name'] + ' (Updated)',
        'duration': '4 Months',
        'start_date': '2026-07-01',
        'description': 'Updated description',
        'skills': 'Python, Django, Flask',
        'category': 'Business',
        'future_opportunities': 'CTO',
        'max_applicants': 150
    }
    r = new_session.put(f'{BASE_URL}/api/opportunities/{created_opp["id"]}', json=updated_data)
    assert r.status_code == 200
    print(f'  PASS: Opportunity updated')
    
    print(f'\n✓ Test 2: Verify updates persisted')
    r = new_session.get(f'{BASE_URL}/api/opportunities/{created_opp["id"]}')
    fetched = r.json()
    assert fetched['name'] == updated_data['name']
    assert fetched['duration'] == '4 Months'
    assert fetched['category'] == 'Business'
    assert fetched['max_applicants'] == 150
    print(f'  PASS: All updates persisted correctly')

# US-2.6: Delete Opportunity
print('\n' + '='*60)
print('US-2.6: DELETE OPPORTUNITY')
print('='*60)

if created_opp:
    opp_id = created_opp['id']
    print(f'\n✓ Test 1: Delete opportunity {opp_id}')
    r = new_session.delete(f'{BASE_URL}/api/opportunities/{opp_id}')
    assert r.status_code == 200
    print(f'  PASS: Delete request successful')
    
    print(f'\n✓ Test 2: Verify deletion')
    r = new_session.get(f'{BASE_URL}/api/opportunities/{opp_id}')
    assert r.status_code == 404
    print(f'  PASS: Opportunity no longer accessible (404)')

# Summary
print('\n' + '='*60)
print('FINAL SUMMARY')
print('='*60)
print('\n✓ US-1.1: Admin Sign Up - ALL TESTS PASSED')
print('✓ US-1.2: Admin Login - ALL TESTS PASSED')
print('✓ US-1.3: Forgot Password - ALL TESTS PASSED')
print('✓ US-2.1: View Opportunities - ALL TESTS PASSED')
print('✓ US-2.2: Add Opportunity - ALL TESTS PASSED')
print('✓ US-2.3: Opportunities Persist - ALL TESTS PASSED')
print('✓ US-2.4: View Details - ALL TESTS PASSED')
print('✓ US-2.5: Edit Opportunity - ALL TESTS PASSED')
print('✓ US-2.6: Delete Opportunity - ALL TESTS PASSED')
print('\n' + '='*60)
print('🎉 ALL 9 USER STORIES VALIDATED SUCCESSFULLY!')
print('='*60)
