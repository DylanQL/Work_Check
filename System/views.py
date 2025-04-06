from django.shortcuts import render, redirect
from functools import wraps
from .models import UserAccount, Usuario, Position, TimeSheetScore, EvaluationCycle

# Decorador personalizado para verificar que el usuario haya iniciado sesión
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view

# Vista de Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password').strip()
        try:
            user_account = UserAccount.objects.get(username=username, password=password)
            if user_account.status != "Activo":
                error = "La cuenta no está activa."
                return render(request, 'System/login.html', {'error': error})
            request.session['user_id'] = user_account.id
            return redirect('home')
        except UserAccount.DoesNotExist:
            error = "Credenciales inválidas."
            return render(request, 'System/login.html', {'error': error})
    return render(request, 'System/login.html')

# Vista para cerrar sesión
def logout_view(request):
    request.session.flush()
    return redirect('login')

# Vista principal (acceso restringido)
@login_required
def home(request):
    return render(request, 'System/home.html')

# Nueva vista para gestionar usuarios (lista de usuarios)
@login_required
def manage_users(request):
    usuarios = Usuario.objects.all()
    return render(request, 'System/manage_users.html', {'usuarios': usuarios})


# Vista para agregar usuarios
@login_required
def add_user(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name').strip()
        second_last_name = request.POST.get('second_last_name', '').strip()
        user_type = request.POST.get('user_type').strip()
        position_id = request.POST.get('position')
        
        # Se crea el registro en la tabla Usuario
        usuario = Usuario.objects.create(
            first_name=first_name,
            middle_name=middle_name if middle_name != '' else None,
            last_name=last_name,
            second_last_name=second_last_name if second_last_name != '' else None,
            user_type=user_type,
            position_id=position_id
        )
        
        # Se crea automáticamente el registro en la tabla TimeSheetScore con score_ts=0
        TimeSheetScore.objects.create(
            usuario=usuario,
            score_ts=0
        )
        
        # Se genera el username concatenando first_name, last_name y second_last_name (si existe), en minúsculas sin espacios
        username = (first_name + last_name + (second_last_name if second_last_name else '')).replace(" ", "").lower()
        default_password = "123456"
        
        # Se crea el registro en la tabla UserAccount
        UserAccount.objects.create(
            username=username,
            password=default_password,
            usuario=usuario,
            status="Activo"
        )
        
        return redirect('home')
    
    positions = Position.objects.all()
    return render(request, 'System/add_user.html', {'positions': positions})

# Vista para actualizar usuarios
@login_required
def update_user(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        return redirect('home')
    
    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name').strip()
        usuario.middle_name = request.POST.get('middle_name', '').strip() or None
        usuario.last_name = request.POST.get('last_name').strip()
        usuario.second_last_name = request.POST.get('second_last_name', '').strip() or None
        usuario.user_type = request.POST.get('user_type').strip()
        usuario.position_id = request.POST.get('position')
        usuario.save()
        
        # Actualización opcional del username en UserAccount
        username = (usuario.first_name + usuario.last_name + (usuario.second_last_name if usuario.second_last_name else '')).replace(" ", "").lower()
        user_account = UserAccount.objects.get(usuario=usuario)
        user_account.username = username
        user_account.save()
        
        return redirect('home')
    
    positions = Position.objects.all()
    return render(request, 'System/update_user.html', {'usuario': usuario, 'positions': positions})


# Vista para listar las cuentas (gestión de UserAccount)
@login_required
def list_accounts(request):
    accounts = UserAccount.objects.all()
    return render(request, 'System/manage_accounts.html', {'accounts': accounts})

# Vista para actualizar una cuenta existente
@login_required
def update_account(request, account_id):
    try:
        account = UserAccount.objects.get(id=account_id)
    except UserAccount.DoesNotExist:
        return redirect('list_accounts')
    
    if request.method == 'POST':
        account.username = request.POST.get('username').strip()
        account.password = request.POST.get('password').strip()
        account.status = request.POST.get('status').strip()
        account.save()
        return redirect('list_accounts')
    
    return render(request, 'System/update_account.html', {'account': account})

# Vista para listar los Timesheet Scores
@login_required
def list_timesheets(request):
    timesheets = TimeSheetScore.objects.all()
    return render(request, 'System/manage_timesheets.html', {'timesheets': timesheets})

# Vista para actualizar un Timesheet Score
@login_required
def update_timesheet(request, timesheet_id):
    try:
        timesheet = TimeSheetScore.objects.get(id=timesheet_id)
    except TimeSheetScore.DoesNotExist:
        return redirect('list_timesheets')
    
    if request.method == 'POST':
        score_value = request.POST.get('score_ts').strip()
        try:
            timesheet.score_ts = int(score_value)
        except ValueError:
            error = "El valor debe ser un número entero."
            return render(request, 'System/update_timesheet.html', {'timesheet': timesheet, 'error': error})
        timesheet.save()
        return redirect('list_timesheets')
    
    return render(request, 'System/update_timesheet.html', {'timesheet': timesheet})

# Vista para listar los ciclos de evaluación
@login_required
def list_evaluation_cycles(request):
    cycles = EvaluationCycle.objects.all()
    return render(request, 'System/manage_evaluation_cycles.html', {'cycles': cycles})

# Vista para crear un nuevo ciclo de evaluación
@login_required
def create_evaluation_cycle(request):
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        if name:
            EvaluationCycle.objects.create(name=name)
            return redirect('list_evaluation_cycles')
        else:
            error = "El nombre es requerido."
            return render(request, 'System/create_evaluation_cycle.html', {'error': error})
    return render(request, 'System/create_evaluation_cycle.html')

# Vista para actualizar un ciclo de evaluación existente
@login_required
def update_evaluation_cycle(request, cycle_id):
    try:
        cycle = EvaluationCycle.objects.get(id=cycle_id)
    except EvaluationCycle.DoesNotExist:
        return redirect('list_evaluation_cycles')
    
    if request.method == 'POST':
        name = request.POST.get('name').strip()
        if name:
            cycle.name = name
            cycle.save()
            return redirect('list_evaluation_cycles')
        else:
            error = "El nombre es requerido."
            return render(request, 'System/update_evaluation_cycle.html', {'cycle': cycle, 'error': error})
    
    return render(request, 'System/update_evaluation_cycle.html', {'cycle': cycle})

# Vista para eliminar un ciclo de evaluación
@login_required
def delete_evaluation_cycle(request, cycle_id):
    try:
        cycle = EvaluationCycle.objects.get(id=cycle_id)
    except EvaluationCycle.DoesNotExist:
        return redirect('list_evaluation_cycles')
    
    if request.method == 'POST':
        cycle.delete()
        return redirect('list_evaluation_cycles')
    
    return render(request, 'System/delete_evaluation_cycle.html', {'cycle': cycle})