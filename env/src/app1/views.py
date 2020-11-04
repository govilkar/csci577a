from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from .models import CommonRegistration, Senior, Caregiver, Posts, Comments, Room, UserChats
import json
from pyzipcode import ZipCodeDatabase

#For messaging
from django.conf import settings
from django.http import JsonResponse


from faker import Faker
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

fake = Faker()

# Create your views here.


def all_rooms(request) :
    rooms = Room.objects.all()
    return render(request, 'chat_index.html', {'rooms': rooms})


def room_detail(request, slug) :
    room = Room.objects.get(slug = slug)
    return render(request, 'chat_room_detail.html',{'room': room})

def token(request):
    # identity = request.GET.get('identity', fake.user_name())
    if request.session['user_type'] == 'senior' :
        user_obj = Senior.objects.get(email = request.session['email'])
    else :
        user_obj = Caregiver.objects.get(email = request.session['email'])
    identity = user_obj.name
    device_id = request.GET.get('device', 'default')  # unique device ID

    account_sid = settings.TWILIO_ACCOUNT_SID
    api_key = settings.TWILIO_API_KEY
    api_secret = settings.TWILIO_API_SECRET
    chat_service_sid = settings.TWILIO_CHAT_SERVICE_SID

    token = AccessToken(account_sid, api_key, api_secret, identity=identity)

    # Create a unique endpoint ID for the device
    endpoint = "MyDjangoChatRoom:{0}:{1}".format(identity, device_id)

    if chat_service_sid:
        chat_grant = ChatGrant(endpoint_id=endpoint,
                               service_sid=chat_service_sid)
        token.add_grant(chat_grant)

    response = {
        'identity': identity,
        'token': token.to_jwt().decode('utf-8')
    }

    return JsonResponse(response)


def add_or_get_chatroom(request, user_id) :

    
    if request.session['user_type'] == 'senior' :
        # If it is a senior requesting to chat to a caregiver
        senior_obj = Senior.objects.get(email = request.session['email'])
        caregiver_obj = Caregiver.objects.get(id = user_id)
        user1_name = senior_obj.name
        user2_name = caregiver_obj.name
        senior_id = senior_obj.id
        caregiver_id = user_id
        chatroom_slug = 'senior_' + str(senior_id) + '_caregiver_' + str(caregiver_id)
    else :
        # If it is a caregiver requesting to chat to a senior
        caregiver_obj = Caregiver.objects.get(email = request.session['email'])
        senior_obj = Senior.objects.get(id = user_id)
        user1_name = caregiver_obj.name
        user2_name = senior_obj.name
        caregiver_id = caregiver_obj.id
        senior_id = user_id
        chatroom_slug = 'senior_' + str(senior_id) + '_caregiver_' + str(caregiver_id)
        pass

    rooms = Room.objects.filter(slug = chatroom_slug)

    if len(rooms) == 0 :
        room_name = 'Chat between ' + user1_name + ' and ' + user2_name
        Room.objects.create(name=room_name, description = ' Description ', slug = chatroom_slug)
        #Add an entry to the UserChats table
        UserChats.objects.create(user = 'senior_' + str(senior_id), chat_slug=chatroom_slug, with_user=caregiver_obj.name)
        UserChats.objects.create(user = 'caregiver_' + str(caregiver_id), chat_slug=chatroom_slug, with_user=senior_obj.name)
        #Redirect to the chatroom

    else :
        # They have chatted previously so no step needed to create a chatroom
        pass

    
    return redirect('room_detail', slug = chatroom_slug)
    # return redirect('all_rooms')


def get_chats(request) :
   
    context = {}
    user_type = request.session['user_type']
    if user_type == 'senior' :
        user_obj = Senior.objects.get(email = request.session['email'])
    else :
        user_obj = Caregiver.objects.get(email = request.session['email'])
    chats = UserChats.objects.filter(user = user_type + "_" + str(user_obj.id))
    
    context['chats'] = chats
    return render(request, 'view_all_chats.html', context)


def logout(request, *args, **kwargs) :
    #Delete the current session variables
    del request.session['user_type']
    del request.session['email']
    del request.session['password']
    return redirect('landing_page')


def view_caregiver_details(request, caregiver_id) :
    # return HttpResponse("<h1> Hey" + str(caregiver_id) + "</h1>")
    context = {}
    caregiver_obj = Caregiver.objects.get(id=caregiver_id)
    context['caregiver'] = caregiver_obj
    return render(request, 'caregiver_details_for_senior.html', context)

def search_caregivers(request, *args, **kwargs) :
    context = {}
    # zcdb = ZipCodeDatabase()
    # in_radius = [z.zip for z in zcdb.get_zipcodes_around_radius('90007', 8)] # ('ZIP', radius in miles)
    # radius_utf = [x.encode('UTF-8') for x in in_radius] # unicode list to utf list
    # context['data'] = radius_utf
    # zip, gender, radius
    if request.method == 'POST' :
        zip_code = request.POST['zip']
        radius = int(request.POST['radius'])
        zcdb = ZipCodeDatabase()
        in_radius = [z.zip for z in zcdb.get_zipcodes_around_radius(zip_code, radius)] # ('ZIP', radius in miles)
        #radius_utf = [x.encode('UTF-8') for x in in_radius] # unicode list to utf list
        radius_arr = [x.encode('utf-8').decode('unicode-escape') for x in in_radius]
        caregivers = Caregiver.objects.filter(zip_code__in = radius_arr)
        context['caregivers'] = caregivers
        context['isPostRequest'] = True
    else :
        context['caregivers'] = []
        context['isPostRequest'] = False
    return render(request, 'search_caregivers.html', context)

def dashboard_view(request, *args, **kwargs) :
    user_type = request.session['user_type']
    if user_type  == 'senior' :
        return redirect('senior_dashboard_view')
    else :
        return redirect('caregiver_dashboard_view')

def caregiver_dashboard_view(request, *args, **kwargs) :
    context = {}
    if request.method == 'POST' :
        name = request.POST['name']
        email = request.POST['email']
        dob = request.POST['dob']
        availability = request.POST['availability']
        zip_code = request.POST['zip']
        city = request.POST['city']
        state = request.POST['state']
        bio = request.POST['bio']

        record = Caregiver.objects.get(email=email)
        record.name = name
        record.availability = availability
        record.zip_code = zip_code
        record.city = city
        record.state = state
        record.bio = bio
        record.dob = dob if dob!="" else None
        record.save()
        context['record'] = record
    else :
        context['record'] = Caregiver.objects.get(email = request.session['email'])
    return render(request, 'caregiver_dashboard.html', context)


def senior_dashboard_view(request, *args, **kwargs) :
    context = {}
    if request.method == 'POST' :
        name = request.POST['name']
        email = request.POST['email']
        dob = request.POST['dob']
        availability = request.POST['availability']
        zip_code = request.POST['zip']
        city = request.POST['city']
        state = request.POST['state']
        bio = request.POST['bio']
        profile_image = request.FILES['profile_image']

        record = Senior.objects.get(email=email)
        record.name = name
        record.availability = availability
        record.zip_code = zip_code
        record.city = city
        record.state = state
        record.bio = bio
        record.dob = dob if dob!="" else None
        record.profile_image = profile_image

        record.save()
        context['record'] = record
        # context['profile_image_url'] = record.profile_image.url
        # context['image_object'] = record.profile_image
    else :
        context['record'] = Senior.objects.get(email = request.session['email'])
        # context['profile_image_url'] = 'default'
        # context['image_object'] = record.profile_image
    return render(request, 'senior_dashboard.html', context)


def add_post_comment(request, *args, **kwargs) :
    post_id = request.GET['comment_for_postId']
    comment_content = request.GET['comment']
    print(request)
    Comments.objects.create(post_id= Posts.objects.get(id=post_id), content = comment_content)
    #return HttpResponse("<h1> Hey, you are about to add a comment for post id = " + post_id + ", with comment = " + comment_content   +  " </h1>")
    return redirect('forum')

def add_new_post(request, *args, **kwargs) :
    # return HttpResponse("<h1> Hey </h1>")
    #Add the content to posts
    Posts.objects.create(created_by=request.POST['email'], content = request.POST['content'], title = request.POST['title'])
    return redirect('forum')

def forum(request, *args, **kwargs) :
    #Get all the current posts
    posts = Posts.objects.all()
    posts_array = []
    for post in posts :
        post_details = {
            'post_id' : post.id,
            'post_created_by': post.created_by ,
            'post_created_at' : post.created_at ,
            'post_content' : post.content ,
            'post_title' : post.title ,
            'post_comments' : Comments.objects.filter(post_id = post.id)
        }
        posts_array.append(post_details)
    context = {
        'posts_array': posts_array
    }
    return render(request, 'forum_page.html', context)

def handle_login(request, *args, **kwargs) :
    #Check if the user exists
    email = request.POST['email']
    password = request.POST['password']
    records = CommonRegistration.objects.filter(email = email)

    if len(records) == 0 :
        return redirect('landing_page')
    else :
        # record = records.first()
        user_type = records.first().userType
        request.session['user_type'] = user_type
        request.session['email'] = email
        request.session['password'] = password
        if user_type == 'senior' :
            record = Senior.objects.get(email = email)
        else :
            record = Caregiver.objects.get(email = email)
        context = {
            'record' : record
        }

        #Add values to the session
        # request.session['isLoggedIn']  = True
        # request.session['email'] = email
        # request.session['userType'] = user_type

        if user_type == 'senior' :
            return render(request, 'senior_dashboard.html', context)
        else :
            return render(request, 'caregiver_dashboard.html', context)
        


def landing_page(request, *args, **kwargs) :
    # return HttpResponse("<h1> Hello Mugdha </h1>")
    context = {}
    if 'email' in request.session :
        #The user is already logged in
        user_type = request.session['user_type']
        email = request.session['email']
        password = request.session['password']
        if user_type == 'senior' :
            context['record'] = Senior.objects.get(email = email)
        else :
            context['record'] = Caregiver.objects.get(email = email)
        return render(request, 'senior_dashboard.html', context)
    else :
        return render(request, 'landing_page.html', context)

def registration_page(request, *args, **kwargs) :
    # return HttpResponse("<h1> Hello Mugdha </h1>")
    context = {}
    if request.method == 'POST' :
        # return HttpResponse("<h1> Response Received </h1>")
        #name = request.POST['name']
        email = request.POST['email']
        password = request.POST['psw']
        user_type = request.POST['optradio']

        record_exists = CommonRegistration.objects.filter(email = email).count() > 0

        if record_exists :
            context['error_msg'] = 'This user exists already'
            return render(request, 'registration_page.html', context)
        else :
            common_registration_obj = CommonRegistration.objects.create(email=email, password=password, userType=user_type)

            if user_type == 'senior' :
                senior_obj = Senior.objects.create(email=email, password=password)
            else :
                caregiver_obj = Caregiver.objects.create(email=email, password=password)
            # return render(request, 'login_page.html', {})
            return redirect('landing_page')


    else :
        return render(request, 'registration_page.html', context)
    


