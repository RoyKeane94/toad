from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Main CRM Home (B2B focused)
    path('', views.crm_home, name='home'),
    
    # ==================== B2B CRM URLS ====================
    path('b2b/', views.crm_home, name='b2b_home'),  # Alias for home
    
    # B2B Company Management
    path('b2b/companies/', views.company_list, name='company_list'),
    path('b2b/companies/create/', views.company_create, name='company_create'),
    path('b2b/companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('b2b/companies/<int:pk>/update/', views.company_update, name='company_update'),
    path('b2b/companies/<int:pk>/delete/', views.company_delete, name='company_delete'),
    path('b2b/sectors/create/', views.company_sector_create, name='company_sector_create'),
    path('b2b/email-templates/', views.email_template_list, name='email_template_list'),
    path('b2b/email-templates/create/', views.email_template_create, name='email_template_create'),
    path('b2b/email-templates/<int:pk>/update/', views.email_template_update, name='email_template_update'),
    path('b2b/email-templates/<int:pk>/delete/', views.email_template_delete, name='email_template_delete'),
    path('b2b/email-templates/<int:pk>/preview/', views.email_template_preview, name='email_template_preview'),
    path('b2b/customer-templates/', views.customer_template_list, name='customer_template_list'),
    path('b2b/customer-templates/create/', views.customer_template_create, name='customer_template_create'),
    path('b2b/customer-templates/<int:pk>/update/', views.customer_template_update, name='customer_template_update'),
    
    # ==================== SOCIETY CRM URLS ====================
    path('society/', views.society_crm_home, name='society_home'),
    path('society/leads/', views.society_lead_list, name='society_lead_list'),
    path('society/leads/create/', views.society_lead_create, name='society_lead_create'),
    path('society/leads/<int:pk>/', views.society_lead_detail, name='society_lead_detail'),
    path('society/leads/<int:pk>/update/', views.society_lead_update, name='society_lead_update'),
    path('society/leads/<int:pk>/delete/', views.society_lead_delete, name='society_lead_delete'),
    
    # Society Links (under society namespace)
    path('society/links/', views.society_link_list, name='society_link_list'),
    path('society/links/create/', views.society_link_create, name='society_link_create'),
    path('society/links/<int:pk>/delete/', views.society_link_delete, name='society_link_delete'),
    path('society/universities/create/', views.society_university_create, name='society_university_create'),
    
    # ==================== LEGACY URLS (for backward compatibility) ====================
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/update/', views.lead_update, name='lead_update'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    
    # ==================== SHARED URLS ====================
    path('leads/<int:lead_pk>/messages/create/', views.lead_message_create, name='lead_message_create'),
    path('b2b/companies/<int:company_pk>/messages/create/', views.company_message_create, name='company_message_create'),
    path('focus/create/', views.lead_focus_create, name='lead_focus_create'),
    path('contact-methods/create/', views.contact_method_create, name='contact_method_create'),
    
    # ==================== PUBLIC URLS ====================
    # Student Society Partnership Pages (MUST come before generic society links)
    path('southampton-economics-society/load-template/', views.load_southampton_economics_template, name='load_southampton_economics_template'),
    path('southampton-economics-society/', views.southampton_economics_society_page, name='southampton_economics_society'),
    

    # Society Links (Public URLs)
    path('<str:university_slug>/<str:society_slug>/', views.society_link_public, name='society_link_public'),
    path('<str:university_slug>/<str:society_slug>/qr/', views.society_link_public_qr, name='society_link_public_qr'),
    path('<str:university_slug>/<str:society_slug>/qr-image/', views.society_link_qr_image, name='society_link_qr_image'),
    # Fallback for old format (temporary)
    path('society-links/<int:pk>/public/', views.society_link_public_old, name='society_link_public_old'),
    
    # Instagram Posts
    path('instagram/', views.instagram_index, name='instagram_index'),
    path('instagram/introducing-toad/', views.instagram_introducing_toad, name='instagram_introducing_toad'),
    path('instagram/why-users-love-toad/', views.instagram_why_users_love_toad, name='instagram_why_users_love_toad'),
    path('instagram/toad-bingo-card/', views.instagram_toad_bingo_card, name='instagram_toad_bingo_card'),
    path('instagram/preview/', views.instagram_preview, name='instagram_preview'),

    # Business links / events
    path('links/events/weddings/', views.toad_weddings_view, name='toad_weddings'),
    path('links/templates/<int:pk>/', views.customer_template_public_view, name='customer_template_public'),
]
