from django.shortcuts import render, redirect
from functools import wraps
from django.contrib import messages
from .models import *

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

# Lista de asignaciones temporales (mostrar solo los registros existentes)
@login_required
def list_temp_evaluation_assignments(request):
    assignments = Temp_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_temp_evaluation_assignments.html', {'assignments': assignments})

# Crear una nueva asignación de evaluación
@login_required
def create_temp_evaluation_assignment(request):
    # Filtrar evaluadores según user_type ("Lider" o "Gerente")
    evaluators = Usuario.objects.filter(user_type__in=["Lider", "Gerente"])
    # Filtrar empleados que sean "Empleado" y que aún no tengan asignación
    assigned_employee_ids = Temp_EvaluationAssignment.objects.values_list('employee_id', flat=True)
    allowed_employee_roles = ["Empleado", "Lider"]
    employees = Usuario.objects.filter(user_type__in=allowed_employee_roles).exclude(id__in=assigned_employee_ids)
    
    if request.method == 'POST':
        evaluator_id = request.POST.get('evaluator')
        employee_id = request.POST.get('employee')
        # Se asigna automáticamente el status "Pendiente"
        status = "Pendiente"
        
        if Temp_EvaluationAssignment.objects.filter(employee_id=employee_id).exists():
            error = "Ya existe una asignación para este empleado."
            return render(request, 'System/create_temp_evaluation_assignment.html', {
                'evaluators': evaluators,
                'employees': employees,
                'error': error
            })
        
        # Obtener el último EvaluationCycle para asignar evaluation_cycle
        last_cycle = EvaluationCycle.objects.order_by('-id').first()
        evaluation_cycle_value = last_cycle.name if last_cycle else ''
        
        Temp_EvaluationAssignment.objects.create(
            evaluator_id=evaluator_id,
            employee_id=employee_id,
            status=status,
            evaluation_cycle=evaluation_cycle_value
        )
        return redirect('list_temp_assignments')
    
    return render(request, 'System/create_temp_evaluation_assignment.html', {
        'evaluators': evaluators,
        'employees': employees
    })



# Actualizar una asignación de evaluación temporal
@login_required
def update_temp_evaluation_assignment(request, assignment_id):
    try:
        assignment = Temp_EvaluationAssignment.objects.get(id=assignment_id)
    except Temp_EvaluationAssignment.DoesNotExist:
        return redirect('list_temp_assignments')
    
    # Filtrar evaluadores según user_type ("Lider" o "Gerente")
    evaluators = Usuario.objects.filter(user_type__in=["Lider", "Gerente"])
    
    if request.method == 'POST':
        evaluator_id = request.POST.get('evaluator')
        # No se actualiza el status, que permanece "Pendiente"
        assignment.evaluator_id = evaluator_id
        assignment.save()
        return redirect('list_temp_assignments')
    
    return render(request, 'System/update_temp_evaluation_assignment.html', {
        'assignment': assignment,
        'evaluators': evaluators
    })



# Eliminar una asignación temporal (opcional, si se requiere)
@login_required
def delete_temp_evaluation_assignment(request, assignment_id):
    try:
        assignment = Temp_EvaluationAssignment.objects.get(id=assignment_id)
    except Temp_EvaluationAssignment.DoesNotExist:
        return redirect('list_temp_evaluation_assignments')
    
    if request.method == 'POST':
        assignment.delete()
        return redirect('list_temp_evaluation_assignments')
    
    return render(request, 'System/delete_temp_evaluation_assignment.html', {'assignment': assignment})

# Enviar registros a histórico:
@login_required
def send_assignments_to_historic(request):
    # Primero, verificar que todos los registros tengan status "Completado"
    assignments = Temp_EvaluationAssignment.objects.all()
    incomplete = assignments.exclude(status="Completado")
    if incomplete.exists():
        messages.error(request, "No todos los usuarios completaron sus evaluaciones.")
        return redirect('list_temp_assignments')
    
    if request.method == 'POST':
        # Copiar cada registro a Permanent_EvaluationAssignment
        for assign in assignments:
            Permanent_EvaluationAssignment.objects.create(
                evaluator=assign.evaluator,
                employee=assign.employee,
                status=assign.status,
                # summary y evaluation_details se dejan como nulos
                evaluation_cycle=assign.evaluation_cycle
            )
        # Borrar todos los registros de Temp_EvaluationAssignment
        assignments.delete()
        messages.success(request, "Registros enviados a histórico correctamente.")
        return redirect('list_temp_assignments')
    
    return render(request, 'System/confirm_send_assignments.html', {})


# Vistas para mostrar los registros históricos (Permanent_EvaluationAssignment)
# y para mostrar el detalle de los registros de Summary y EvaluationDetails.

@login_required
def list_permanent_assignments(request):
    """
    Lista todos los registros históricos de evaluaciones permanentes.
    Se muestra una tabla con los registros; en los campos 'summary' y 'evaluation_details'
    se incluyen enlaces a la vista de detalle correspondiente si existe el registro.
    """
    assignments = Permanent_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_permanent_assignments.html', {'assignments': assignments})

@login_required
def detail_summary(request, summary_id):
    """
    Muestra el detalle de un registro Summary.
    Si no se encuentra el registro, redirige a la lista de asignaciones permanentes.
    """
    try:
        summary = Summary.objects.get(id=summary_id)
    except Summary.DoesNotExist:
        return redirect('list_permanent_assignments')
    return render(request, 'System/detail_summary.html', {'summary': summary})

@login_required
def detail_evaluation_details(request, evaluation_details_id):
    """
    Muestra el detalle de un registro EvaluationDetails.
    Si el registro no existe, redirige a la lista de asignaciones permanentes.
    """
    try:
        details = EvaluationDetails.objects.get(id=evaluation_details_id)
    except EvaluationDetails.DoesNotExist:
        return redirect('list_permanent_assignments')
    return render(request, 'System/detail_evaluation_details.html', {'details': details})


@login_required
def leaders_evaluations(request):
    """
    Muestra las evaluaciones de líderes.
    
    Se filtran los registros de Permanent_EvaluationAssignment cuyo 
    Summary asociado tenga evaluation_type igual a "Lideres".
    De cada registro se muestra:
      - Desde Permanent_EvaluationAssignment: evaluation_cycle.
      - Desde Summary: employee, evaluator, R, L, H, E, C, M, V, final_score, performance_level y position.
    """
    assignments = Permanent_EvaluationAssignment.objects.filter(summary__evaluation_type="Lideres")
    return render(request, 'System/leaders_evaluations.html', {'assignments': assignments})
