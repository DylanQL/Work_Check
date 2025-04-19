from django.shortcuts import render, redirect, get_object_or_404
from functools import wraps
from django.contrib import messages
from .models import *
from django.db import transaction
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, DeleteView
from django.views import View
from .forms import PositionForm, UserTemplateAssignForm, UserTemplateEditForm 
from django.db import transaction
from .models import EvaluationDetails
from django.utils.decorators import method_decorator


# Decorador personalizado para verificar que el usuario haya iniciado sesión
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapped_view

# Decorador parametrizado que acepta varios roles permitidos
def roles_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Verificar si el usuario ha iniciado sesión
            if not request.session.get('user_id'):
                return redirect('login')

            user_id = request.session.get('user_id')
            try:
                user_account = UserAccount.objects.get(id=user_id)
                usuario = user_account.usuario
                # Si el tipo de usuario no está en la lista de roles permitidos, denegar acceso
                if usuario.user_type not in allowed_roles:
                    messages.error(request, 
                        f"Acceso denegado. Solo los usuarios con los roles {', '.join(allowed_roles)} pueden acceder a esta página."
                    )
                    return redirect('login')
            except UserAccount.DoesNotExist:
                return redirect('login')

            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


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
            # Guardar el ID y el tipo de usuario en la sesión
            request.session['user_id'] = user_account.id
            request.session['user_type'] = user_account.usuario.user_type
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
    user_id = request.session.get('user_id')
    user_account = UserAccount.objects.get(id=user_id)
    usuario = user_account.usuario
    return render(request, 'System/home.html', {'usuario': usuario})

# Nueva vista para gestionar usuarios (lista de usuarios)
@roles_required("Administrador")
def manage_users(request):
    usuarios = Usuario.objects.all()
    return render(request, 'System/manage_users.html', {'usuarios': usuarios})


# Vista para agregar usuarios
@roles_required("Administrador")
def add_user(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        last_name = request.POST.get('last_name').strip()
        second_last_name = request.POST.get('second_last_name', '').strip()
        dni = request.POST.get('dni').strip()
        user_type = request.POST.get('user_type').strip()
        position_id = request.POST.get('position')
        
        # Se crea el registro en la tabla Usuario
        usuario = Usuario.objects.create(
            first_name=first_name,
            middle_name=middle_name if middle_name != '' else None,
            last_name=last_name,
            second_last_name=second_last_name if second_last_name != '' else None,
            dni=dni,
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
        
        return redirect('manage_users')
    
    positions = Position.objects.all()
    return render(request, 'System/add_user.html', {'positions': positions})

# Vista para actualizar usuarios
@roles_required("Administrador")
def update_user(request, user_id):
    try:
        usuario = Usuario.objects.get(id=user_id)
    except Usuario.DoesNotExist:
        return redirect('manage_users')
    
    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name').strip()
        usuario.middle_name = request.POST.get('middle_name', '').strip() or None
        usuario.last_name = request.POST.get('last_name').strip()
        usuario.second_last_name = request.POST.get('second_last_name', '').strip() or None
        usuario.dni = request.POST.get('dni').strip()
        usuario.user_type = request.POST.get('user_type').strip()
        usuario.position_id = request.POST.get('position')
        usuario.save()
        
        # Actualización opcional del username en UserAccount
        username = (usuario.first_name + usuario.last_name + (usuario.second_last_name if usuario.second_last_name else '')).replace(" ", "").lower()
        user_account = UserAccount.objects.get(usuario=usuario)
        user_account.username = username
        user_account.save()
        
        return redirect('manage_users')
    
    positions = Position.objects.all()
    return render(request, 'System/update_user.html', {'usuario': usuario, 'positions': positions})


# Vista para listar las cuentas (gestión de UserAccount)
@roles_required("Administrador")
def list_accounts(request):
    accounts = UserAccount.objects.all()
    return render(request, 'System/manage_accounts.html', {'accounts': accounts})

# Vista para actualizar una cuenta existente
@roles_required("Administrador")
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
@roles_required("Administrador")
def list_timesheets(request):
    timesheets = TimeSheetScore.objects.all()
    return render(request, 'System/manage_timesheets.html', {'timesheets': timesheets})

# Vista para actualizar un Timesheet Score
@roles_required("Administrador")
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
@roles_required("Administrador")
def list_evaluation_cycles(request):
    cycles = EvaluationCycle.objects.all()
    return render(request, 'System/manage_evaluation_cycles.html', {'cycles': cycles})

# Vista para crear un nuevo ciclo de evaluación
@roles_required("Administrador")
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
@roles_required("Administrador")
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
@roles_required("Administrador")
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
@roles_required("Administrador")
def list_temp_evaluation_assignments(request):
    assignments = Temp_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_temp_evaluation_assignments.html', {'assignments': assignments})

# Crear una nueva asignación de evaluación
@roles_required("Administrador")
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
@roles_required("Administrador")
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
@roles_required("Administrador")
def delete_temp_evaluation_assignment(request, assignment_id):
    try:
        assignment = Temp_EvaluationAssignment.objects.get(id=assignment_id)
    except Temp_EvaluationAssignment.DoesNotExist:
        return redirect('list_temp_assignments')
    
    if request.method == 'POST':
        assignment.delete()
        return redirect('list_temp_assignments')
    
    return render(request, 'System/delete_temp_evaluation_assignment.html', {'assignment': assignment})

# Enviar registros a histórico:
@roles_required("Administrador")
def send_assignments_to_historic(request):
    """
    Envía los registros de Temp_EvaluationAssignment a Permanent_EvaluationAssignment.
    
    Requisitos:
      - Todos los registros deben tener status "Completado".
      - Cada registro debe tener asignado un Summary y un EvaluationDetails.
      
    Si se cumplen, se crea un registro en Permanent_EvaluationAssignment copiando:
      evaluator, employee, status, evaluation_cycle, summary y evaluation_details.
    Luego se eliminan los registros de Temp_EvaluationAssignment.
    """
    # Obtener todas las asignaciones temporales
    assignments = Temp_EvaluationAssignment.objects.all()
    
    # Verificar que todos tengan status "Completado"
    incomplete = assignments.exclude(status="Completado")
    if incomplete.exists():
        messages.error(request, "No todos los usuarios completaron sus evaluaciones.")
        return redirect('list_temp_assignments')
    
    if request.method == 'POST':
        # Iterar sobre cada asignación temporal
        for assign in assignments:
            # Verificar que tenga un Summary asociado
            if not assign.summary:
                messages.error(
                    request,
                    f"La asignación para el empleado {assign.employee.first_name} {assign.employee.last_name} no tiene Summary asignado."
                )
                return redirect('list_temp_assignments')
            # Verificar que tenga EvaluationDetails asociado
            if not assign.evaluation_details:
                messages.error(
                    request,
                    f"La asignación para el empleado {assign.employee.first_name} {assign.employee.last_name} no tiene Evaluation Details asignado."
                )
                return redirect('list_temp_assignments')
            
            # Crear registro en Permanent_EvaluationAssignment
            Permanent_EvaluationAssignment.objects.create(
                evaluator=assign.evaluator,
                employee=assign.employee,
                status=assign.status,
                evaluation_cycle=assign.evaluation_cycle,
                summary=assign.summary,
                evaluation_details=assign.evaluation_details  # Se copia el EvaluationDetails
            )
        # Eliminar todos los registros temporales
        assignments.delete()
        messages.success(request, "Registros enviados a histórico correctamente.")
        return redirect('list_temp_assignments')
    
    return render(request, 'System/confirm_send_assignments.html', {})


# Vistas para mostrar los registros históricos (Permanent_EvaluationAssignment)
# y para mostrar el detalle de los registros de Summary y EvaluationDetails.

@roles_required("Administrador")
def list_permanent_assignments(request):
    """
    Lista todos los registros históricos de evaluaciones permanentes.
    Se muestra una tabla con los registros; en los campos 'summary' y 'evaluation_details'
    se incluyen enlaces a la vista de detalle correspondiente si existe el registro.
    """
    assignments = Permanent_EvaluationAssignment.objects.all()
    return render(request, 'System/manage_permanent_assignments.html', {'assignments': assignments})

@roles_required("Administrador")
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

@roles_required("Administrador")
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


@roles_required("Administrador")
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
       
    # Redondear los valores a dos decimales
    for assignment in assignments:
        summary = assignment.summary
        if summary:
            summary.R = round(summary.R, 2) if summary.R is not None else None
            summary.L = round(summary.L, 2) if summary.L is not None else None
            summary.H = round(summary.H, 2) if summary.H is not None else None
            summary.E = round(summary.E, 2) if summary.E is not None else None
            summary.C = round(summary.C, 2) if summary.C is not None else None
            summary.M = round(summary.M, 2) if summary.M is not None else None
            summary.V = round(summary.V, 2) if summary.V is not None else None
            summary.final_score = round(summary.final_score, 2) if summary.final_score is not None else None

    return render(request, 'System/leaders_evaluations.html', {'assignments': assignments})

@roles_required("Administrador")
def employees_evaluations(request):
    """
    Muestra las evaluaciones de empleados.
    
    Se filtran los registros de Permanent_EvaluationAssignment cuyo registro
    asociado de Summary tenga evaluation_type igual a "Empleados". De cada registro,
    se muestran:
      - Desde Permanent_EvaluationAssignment: evaluation_cycle.
      - Desde Summary: employee, evaluator, R, H, E, C, M, V, final_score,
        performance_level y position.
    """
    assignments = Permanent_EvaluationAssignment.objects.filter(summary__evaluation_type="Empleados")
    
    # Redondear los valores a dos decimales
    for assignment in assignments:
        summary = assignment.summary
        if summary:
            summary.R = round(summary.R, 2) if summary.R is not None else None
            summary.L = round(summary.L, 2) if summary.L is not None else None
            summary.H = round(summary.H, 2) if summary.H is not None else None
            summary.E = round(summary.E, 2) if summary.E is not None else None
            summary.C = round(summary.C, 2) if summary.C is not None else None
            summary.M = round(summary.M, 2) if summary.M is not None else None
            summary.V = round(summary.V, 2) if summary.V is not None else None
            summary.final_score = round(summary.final_score, 2) if summary.final_score is not None else None
            
    return render(request, 'System/employees_evaluations.html', {'assignments': assignments})

def safe_get(post_data, key):
    value = post_data.get(key)
    return int(value) if value is not None and value.strip() != '' else None

@roles_required("Gerente")
def evaluate_leaders(request):
    
    """
    Muestra y procesa un formulario para evaluar a líderes.
    - Solo se pueden evaluar usuarios que estén en Temp_EvaluationAssignment
      asignados al usuario logueado.
    - Se asigna la posición automáticamente al seleccionar el usuario a evaluar.
    - Si el status en Temp_EvaluationAssignment es 'Completado', se cargan
      los datos de EvaluationDetails para edición.
    - Al enviar el formulario, se crean/actualizan los registros en 
      EvaluationDetails y Summary, y se actualiza Temp_EvaluationAssignment.
    """
    # 1. Obtener el usuario logueado y sus asignaciones
    current_user_id = request.session.get('user_id')
    # Encontrar al usuario en la tabla UserAccount para relacionar con la tabla Usuario
    # asumiendo que el campo user_id en session corresponde a un UserAccount
    from .models import UserAccount
    try:
        current_user_account = UserAccount.objects.get(id=current_user_id)
        current_usuario = current_user_account.usuario
    except UserAccount.DoesNotExist:
        return redirect('login')

    # Filtrar asignaciones temporales donde el evaluador sea el usuario logueado
    temp_assignments = Temp_EvaluationAssignment.objects.filter(evaluator=current_usuario)

    # Obtener la lista de usuarios (employee) asignados a este evaluador
    # (solo su ID y su nombre para mostrar en el select)
    assigned_employees = [assignment.employee for assignment in temp_assignments]

    # Preparamos un diccionario para mapear employee_id -> assignment
    assignment_by_employee = {a.employee.id: a for a in temp_assignments}

    # 2. Manejo de la selección del usuario y carga de datos
    selected_employee_id = request.GET.get('employee_id', '')
    selected_employee = None
    assignment_selected = None
    evaluation_details_data = {}
    status_already_completed = False

    if selected_employee_id:
        try:
            selected_employee_id = int(selected_employee_id)
            selected_employee = current_usuario.__class__.objects.get(id=selected_employee_id)
            # Obtener la asignación
            assignment_selected = assignment_by_employee.get(selected_employee_id)
            if assignment_selected and assignment_selected.status == "Completado":
                # Cargar los datos de la EvaluationDetails existente
                if assignment_selected.evaluation_details:
                    ed = assignment_selected.evaluation_details
                    status_already_completed = True
                    # Convertir el objeto a diccionario para precargar en el formulario
                    evaluation_details_data = {
                        'R1': ed.R1, 'R2': ed.R2, 'R3': ed.R3, 'R4': ed.R4, 'R5': ed.R5,
                        'R_comments': ed.R_comments,
                        'L1': ed.L1, 'L2': ed.L2, 'L3': ed.L3, 'L4': ed.L4, 'L5': ed.L5,
                        'L_comments': ed.L_comments,
                        'H1': ed.H1, 'H2': ed.H2, 'H3': ed.H3, 'H4': ed.H4, 'H5': ed.H5,
                        'H_comments': ed.H_comments,
                        'E1': ed.E1, 'E2': ed.E2, 'E3': ed.E3, 'E4': ed.E4,
                        'E_comments': ed.E_comments,
                        'C1': ed.C1, 'C2': ed.C2, 'C3': ed.C3, 'C4': ed.C4, 'C5': ed.C5, 'C6': ed.C6,
                        'C_comments': ed.C_comments,
                        'M1': ed.M1, 'M2': ed.M2,
                        'M_comments': ed.M_comments,
                        'V1': ed.V1, 'V2': ed.V2, 'V3': ed.V3, 'V4': ed.V4, 'V5': ed.V5,
                        'V_comments': ed.V_comments,
                        'final_comments': ed.final_comments
                    }
        except (ValueError, Usuario.DoesNotExist):
            selected_employee = None

    # Obtener el TimeSheetScore del usuario seleccionado
    try:
        timesheet_score = TimeSheetScore.objects.get(usuario=selected_employee)
        score_ts_value = timesheet_score.score_ts
    except TimeSheetScore.DoesNotExist:
        score_ts_value = 0

    # Si no hay detalles de evaluación, inicializar con valores por defecto
    if not evaluation_details_data:
        evaluation_details_data = {
            'R5': score_ts_value
        }

    # 3. Procesamiento del formulario en POST
    if request.method == 'POST':
        # Se asume que el usuario a evaluar viene en un campo hidden
        employee_id_post = request.POST.get('employee_id')
        try:
            employee_id_post = int(employee_id_post)
        except (ValueError, TypeError):
            employee_id_post = None
        
        # Recogemos todos los campos
        R1 = safe_get(request.POST, 'R1')
        R2 = safe_get(request.POST, 'R2')
        R3 = safe_get(request.POST, 'R3')
        R4 = safe_get(request.POST, 'R4')
        R5 = safe_get(request.POST, 'R5')
        R_comments = request.POST.get('R_comments', '')

        L1 = safe_get(request.POST, 'L1')
        L2 = safe_get(request.POST, 'L2')
        L3 = safe_get(request.POST, 'L3')
        L4 = safe_get(request.POST, 'L4')
        L5 = safe_get(request.POST, 'L5')
        L_comments = request.POST.get('L_comments', '')

        H1 = safe_get(request.POST, 'H1')
        H2 = safe_get(request.POST, 'H2')
        H3 = safe_get(request.POST, 'H3')
        H4 = safe_get(request.POST, 'H4')
        H5 = safe_get(request.POST, 'H5')
        H_comments = request.POST.get('H_comments', '')

        E1 = safe_get(request.POST, 'E1')
        E2 = safe_get(request.POST, 'E2')
        E3 = safe_get(request.POST, 'E3')
        E4 = safe_get(request.POST, 'E4')
        E_comments = request.POST.get('E_comments', '')

        C1 = safe_get(request.POST, 'C1')
        C2 = safe_get(request.POST, 'C2')
        C3 = safe_get(request.POST, 'C3')
        C4 = safe_get(request.POST, 'C4')
        C5 = safe_get(request.POST, 'C5')
        C6 = safe_get(request.POST, 'C6')
        C_comments = request.POST.get('C_comments', '')

        M1 = safe_get(request.POST, 'M1')
        M2 = safe_get(request.POST, 'M2')
        M_comments = request.POST.get('M_comments', '')

        V1 = safe_get(request.POST, 'V1')
        V2 = safe_get(request.POST, 'V2')
        V3 = safe_get(request.POST, 'V3')
        V4 = safe_get(request.POST, 'V4')
        V5 = safe_get(request.POST, 'V5')
        V_comments = request.POST.get('V_comments', '')

        final_comments = request.POST.get('final_comments', '')

        button_clicked = request.POST.get('action')

        if button_clicked == "Limpiar formulario":
            return redirect('evaluate_leaders')  # o la URL que quieras recargar

        # Si se hace clic en "Enviar formulario"
        if button_clicked == "Enviar formulario" and employee_id_post:
            with transaction.atomic():
                assignment = assignment_by_employee.get(employee_id_post)
                if not assignment:
                    return redirect('evaluate_leaders')

                if assignment.evaluation_details:
                    ed = assignment.evaluation_details
                else:
                    ed = EvaluationDetails()

                ed.R1 = R1; ed.R2 = R2; ed.R3 = R3; ed.R4 = R4; ed.R5 = R5; ed.R_comments = R_comments
                ed.L1 = L1; ed.L2 = L2; ed.L3 = L3; ed.L4 = L4; ed.L5 = L5; ed.L_comments = L_comments
                ed.H1 = H1; ed.H2 = H2; ed.H3 = H3; ed.H4 = H4; ed.H5 = H5; ed.H_comments = H_comments
                ed.E1 = E1; ed.E2 = E2; ed.E3 = E3; ed.E4 = E4; ed.E_comments = E_comments
                ed.C1 = C1; ed.C2 = C2; ed.C3 = C3; ed.C4 = C4; ed.C5 = C5; ed.C6 = C6; ed.C_comments = C_comments
                ed.M1 = M1; ed.M2 = M2; ed.M_comments = M_comments
                ed.V1 = V1; ed.V2 = V2; ed.V3 = V3; ed.V4 = V4; ed.V5 = V5; ed.V_comments = V_comments
                ed.final_comments = final_comments
                ed.save()

                assignment.evaluation_details = ed

                # 2. Crear/actualizar Summary
                # Calcular promedios
                def avg(*values):
                    valid = [int(v) for v in values if v is not None]
                    return sum(valid)/len(valid) if valid else None

                R_avg = avg(R1, R2, R3, R4, R5)
                L_avg = avg(L1, L2, L3, L4, L5)
                H_avg = avg(H1, H2, H3, H4, H5)
                E_avg = avg(E1, E2, E3, E4)
                C_avg = avg(C1, C2, C3, C4, C5, C6)
                M_avg = avg(M1, M2)
                
                # V is a sum, not an average
                V_values = [safe_get(request.POST, f'V{i}') for i in range(1, 6)]
                V_valid = [int(v) for v in V_values if v is not None]
                V_sum = sum(V_valid) if V_valid else None

                # Valores base
                w_R = 0.20
                w_L = 0.20
                w_H = 0.10
                w_E = 0.10
                w_C = 0.15
                w_M = 0.15
                w_V = 0.10

                # Ajustar peso si no hay L
                if L_avg is None:
                    w_R += w_L
                    w_L = 0  # ya no se usa

                # Cálculo
                weighted_sum = 0
                total_weight = 0

                if R_avg is not None:
                    weighted_sum += R_avg * w_R
                    total_weight += w_R
                if L_avg is not None:
                    weighted_sum += L_avg * w_L
                    total_weight += w_L
                if H_avg is not None:
                    weighted_sum += H_avg * w_H
                    total_weight += w_H
                if E_avg is not None:
                    weighted_sum += E_avg * w_E
                    total_weight += w_E
                if C_avg is not None:
                    weighted_sum += C_avg * w_C
                    total_weight += w_C
                if M_avg is not None:
                    weighted_sum += M_avg * w_M
                    total_weight += w_M
                if V_sum is not None:
                    weighted_sum += V_sum * w_V
                    total_weight += w_V

                final_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else None

                # Performance_level basado en final_score con los niveles
                if final_score >= 4.50 and final_score <= 5.00:
                    performance_level = "Nivel 5"
                elif final_score >= 3.50 and final_score <= 4.49:
                    performance_level = "Nivel 4"
                elif final_score >= 2.75 and final_score <= 3.49:
                    performance_level = "Nivel 3"
                elif final_score >= 2.00 and final_score <= 2.74:
                    performance_level = "Nivel 2"
                else:
                    performance_level = "Nivel 1"

                # Buscar o crear Summary
                if assignment.summary:
                    summ = assignment.summary
                else:
                    summ = Summary()

                # Rellenar summary
                summ.employee = assignment.employee
                summ.evaluator = assignment.evaluator
                summ.R = R_avg
                summ.L = L_avg
                summ.H = H_avg
                summ.E = E_avg
                summ.C = C_avg
                summ.M = M_avg
                summ.V = V_sum  # Store the sum, not the average
                summ.final_score = final_score
                summ.performance_level = performance_level
                summ.evaluation_type = "Lideres"  # Se asume que es para líderes
                # Se obtiene la posición del empleado
                summ.position = assignment.employee.position
                summ.save()

                assignment.summary = summ
                # Actualizar status
                assignment.status = "Completado"
                assignment.save()

            return redirect('evaluate_leaders')  # O a otra URL de confirmación

    context = {
        'assigned_employees': assigned_employees,
        'selected_employee': selected_employee,
        'evaluation_details_data': evaluation_details_data,
        'status_already_completed': status_already_completed
    }
    return render(request, 'evaluations/evaluate_leaders.html', context)

@roles_required("Lider")
def evaluate_employees(request):
    """
    Vista para evaluar a empleados.
    
    Solo se muestran los empleados asignados al evaluador logueado (de Temp_EvaluationAssignment) 
    cuyo user_type sea "Empleado". Si la asignación ya tiene status "Completado", se precargan los datos
    de EvaluationDetails para editar.
    
    Al enviar el formulario se crean o actualizan los registros en 
    EvaluationDetails y Summary, y se actualiza el registro de Temp_EvaluationAssignment con los IDs correspondientes y se marca como "Completado".
    
    Los ponderados para el cálculo son:
      - Responsabilidades de la posición (R): 0.40
      - Habilidades (H): 0.10
      - Enfoque (E): 0.10
      - Competencia Técnica (C): 0.15
      - Metas y Resultados (M): 0.15
      - Valores Corporativos (V): 0.10
    """
    # Obtener el usuario logueado (asumimos que el user_id en sesión corresponde a un UserAccount)
    current_user_id = request.session.get('user_id')
    from .models import UserAccount  # Asegúrate de tener importado UserAccount
    try:
        current_user_account = UserAccount.objects.get(id=current_user_id)
        current_usuario = current_user_account.usuario
    except UserAccount.DoesNotExist:
        return redirect('login')

    # Filtrar asignaciones temporales donde el evaluador sea el usuario logueado y el empleado tenga user_type "Empleado"
    temp_assignments = Temp_EvaluationAssignment.objects.filter(evaluator=current_usuario, employee__user_type="Empleado")
    
    # Lista de empleados asignados
    assigned_employees = [assignment.employee for assignment in temp_assignments]
    # Mapeo: employee_id -> asignación
    assignment_by_employee = {a.employee.id: a for a in temp_assignments}

    # Capturar el empleado seleccionado vía GET
    selected_employee_id = request.GET.get('employee_id', '')
    selected_employee = None
    assignment_selected = None
    evaluation_details_data = {}
    status_already_completed = False

    if selected_employee_id:
        try:
            selected_employee_id = int(selected_employee_id)
            selected_employee = current_usuario.__class__.objects.get(id=selected_employee_id)
            # Obtener la asignación
            assignment_selected = assignment_by_employee.get(selected_employee_id)
            if assignment_selected and assignment_selected.status == "Completado":
                # Cargar los datos de la EvaluationDetails existente
                if assignment_selected.evaluation_details:
                    ed = assignment_selected.evaluation_details
                    status_already_completed = True
                    # Convertir el objeto a diccionario para precargar en el formulario
                    evaluation_details_data = {
                        'R1': ed.R1, 'R2': ed.R2, 'R3': ed.R3, 'R4': ed.R4, 'R5': ed.R5,
                        'R_comments': ed.R_comments,
                        'L1': ed.L1, 'L2': ed.L2, 'L3': ed.L3, 'L4': ed.L4, 'L5': ed.L5,
                        'L_comments': ed.L_comments,
                        'H1': ed.H1, 'H2': ed.H2, 'H3': ed.H3, 'H4': ed.H4, 'H5': ed.H5,
                        'H_comments': ed.H_comments,
                        'E1': ed.E1, 'E2': ed.E2, 'E3': ed.E3, 'E4': ed.E4,
                        'E_comments': ed.E_comments,
                        'C1': ed.C1, 'C2': ed.C2, 'C3': ed.C3, 'C4': ed.C4, 'C5': ed.C5, 'C6': ed.C6,
                        'C_comments': ed.C_comments,
                        'M1': ed.M1, 'M2': ed.M2,
                        'M_comments': ed.M_comments,
                        'V1': ed.V1, 'V2': ed.V2, 'V3': ed.V3, 'V4': ed.V4, 'V5': ed.V5,
                        'V_comments': ed.V_comments,
                        'final_comments': ed.final_comments
                    }
        except (ValueError, Usuario.DoesNotExist):
            selected_employee = None

    # Obtener el TimeSheetScore del usuario seleccionado
    try:
        timesheet_score = TimeSheetScore.objects.get(usuario=selected_employee)
        score_ts_value = timesheet_score.score_ts
    except TimeSheetScore.DoesNotExist:
        score_ts_value = 0

    # Si no hay detalles de evaluación, inicializar con valores por defecto
    if not evaluation_details_data:
        evaluation_details_data = {
            'R5': score_ts_value
        }

    # Procesar el envío del formulario
    if request.method == 'POST':
        # Se asume que se envía un campo hidden "employee_id"
        employee_id_post = request.POST.get('employee_id')
        try:
            employee_id_post = int(employee_id_post)
        except (ValueError, TypeError):
            employee_id_post = None

        # Recogemos todos los campos
        R1 = safe_get(request.POST, 'R1')
        R2 = safe_get(request.POST, 'R2')
        R3 = safe_get(request.POST, 'R3')
        R4 = safe_get(request.POST, 'R4')
        R5 = safe_get(request.POST, 'R5')
        R_comments = request.POST.get('R_comments', '')

        L1 = safe_get(request.POST, 'L1')
        L2 = safe_get(request.POST, 'L2')
        L3 = safe_get(request.POST, 'L3')
        L4 = safe_get(request.POST, 'L4')
        L5 = safe_get(request.POST, 'L5')
        L_comments = request.POST.get('L_comments', '')

        H1 = safe_get(request.POST, 'H1')
        H2 = safe_get(request.POST, 'H2')
        H3 = safe_get(request.POST, 'H3')
        H4 = safe_get(request.POST, 'H4')
        H5 = safe_get(request.POST, 'H5')
        H_comments = request.POST.get('H_comments', '')

        E1 = safe_get(request.POST, 'E1')
        E2 = safe_get(request.POST, 'E2')
        E3 = safe_get(request.POST, 'E3')
        E4 = safe_get(request.POST, 'E4')
        E_comments = request.POST.get('E_comments', '')

        C1 = safe_get(request.POST, 'C1')
        C2 = safe_get(request.POST, 'C2')
        C3 = safe_get(request.POST, 'C3')
        C4 = safe_get(request.POST, 'C4')
        C5 = safe_get(request.POST, 'C5')
        C6 = safe_get(request.POST, 'C6')
        C_comments = request.POST.get('C_comments', '')

        M1 = safe_get(request.POST, 'M1')
        M2 = safe_get(request.POST, 'M2')
        M_comments = request.POST.get('M_comments', '')

        V1 = safe_get(request.POST, 'V1')
        V2 = safe_get(request.POST, 'V2')
        V3 = safe_get(request.POST, 'V3')
        V4 = safe_get(request.POST, 'V4')
        V5 = safe_get(request.POST, 'V5')
        V_comments = request.POST.get('V_comments', '')

        final_comments = request.POST.get('final_comments', '')
        
        button_clicked = request.POST.get('action')
        if button_clicked == "Limpiar formulario":
            return redirect('evaluate_employees')

        # Si se hace clic en "Enviar formulario"
        if button_clicked == "Enviar formulario" and employee_id_post:
            with transaction.atomic():
                assignment = assignment_by_employee.get(employee_id_post)
                if not assignment:
                    return redirect('evaluate_leaders')

                if assignment.evaluation_details:
                    ed = assignment.evaluation_details
                else:
                    ed = EvaluationDetails()

                ed.R1 = R1; ed.R2 = R2; ed.R3 = R3; ed.R4 = R4; ed.R5 = R5; ed.R_comments = R_comments
                ed.L1 = L1; ed.L2 = L2; ed.L3 = L3; ed.L4 = L4; ed.L5 = L5; ed.L_comments = L_comments
                ed.H1 = H1; ed.H2 = H2; ed.H3 = H3; ed.H4 = H4; ed.H5 = H5; ed.H_comments = H_comments
                ed.E1 = E1; ed.E2 = E2; ed.E3 = E3; ed.E4 = E4; ed.E_comments = E_comments
                ed.C1 = C1; ed.C2 = C2; ed.C3 = C3; ed.C4 = C4; ed.C5 = C5; ed.C6 = C6; ed.C_comments = C_comments
                ed.M1 = M1; ed.M2 = M2; ed.M_comments = M_comments
                ed.V1 = V1; ed.V2 = V2; ed.V3 = V3; ed.V4 = V4; ed.V5 = V5; ed.V_comments = V_comments
                ed.final_comments = final_comments
                ed.save()

                assignment.evaluation_details = ed

                # 2. Crear/actualizar Summary
                # Calcular promedios
                def avg(*values):
                    valid = [int(v) for v in values if v is not None]
                    return sum(valid)/len(valid) if valid else None

                R_avg = avg(R1, R2, R3, R4, R5)
                L_avg = avg(L1, L2, L3, L4, L5)
                H_avg = avg(H1, H2, H3, H4, H5)
                E_avg = avg(E1, E2, E3, E4)
                C_avg = avg(C1, C2, C3, C4, C5, C6)
                M_avg = avg(M1, M2)
                
                # V is a sum, not an average
                V_values = [safe_get(request.POST, f'V{i}') for i in range(1, 6)]
                V_valid = [int(v) for v in V_values if v is not None]
                V_sum = sum(V_valid) if V_valid else None

                # Valores base
                w_R = 0.20
                w_L = 0.20
                w_H = 0.10
                w_E = 0.10
                w_C = 0.15
                w_M = 0.15
                w_V = 0.10

                # Ajustar peso si no hay L
                if L_avg is None:
                    w_R += w_L
                    w_L = 0  # ya no se usa

                # Cálculo
                weighted_sum = 0
                total_weight = 0

                if R_avg is not None:
                    weighted_sum += R_avg * w_R
                    total_weight += w_R
                if L_avg is not None:
                    weighted_sum += L_avg * w_L
                    total_weight += w_L
                if H_avg is not None:
                    weighted_sum += H_avg * w_H
                    total_weight += w_H
                if E_avg is not None:
                    weighted_sum += E_avg * w_E
                    total_weight += w_E
                if C_avg is not None:
                    weighted_sum += C_avg * w_C
                    total_weight += w_C
                if M_avg is not None:
                    weighted_sum += M_avg * w_M
                    total_weight += w_M
                if V_sum is not None:
                    weighted_sum += V_sum * w_V
                    total_weight += w_V

                final_score = round(weighted_sum / total_weight, 2) if total_weight > 0 else None

                # Performance_level basado en final_score con los niveles
                if final_score >= 4.50 and final_score <= 5.00:
                    performance_level = "Nivel 5"
                elif final_score >= 3.50 and final_score <= 4.49:
                    performance_level = "Nivel 4"
                elif final_score >= 2.75 and final_score <= 3.49:
                    performance_level = "Nivel 3"
                elif final_score >= 2.00 and final_score <= 2.74:
                    performance_level = "Nivel 2"
                else:
                    performance_level = "Nivel 1"

                # Buscar o crear Summary
                if assignment.summary:
                    summ = assignment.summary
                else:
                    summ = Summary()

                # Rellenar summary
                summ.employee = assignment.employee
                summ.evaluator = assignment.evaluator
                summ.R = R_avg
                summ.L = L_avg
                summ.H = H_avg
                summ.E = E_avg
                summ.C = C_avg
                summ.M = M_avg
                summ.V = V_sum  # Store the sum, not the average
                summ.final_score = final_score
                summ.performance_level = performance_level
                summ.evaluation_type = "Lideres"  # Se asume que es para líderes
                # Se obtiene la posición del empleado
                summ.position = assignment.employee.position
                summ.save()

                assignment.summary = summ
                # Actualizar status
                assignment.status = "Completado"
                assignment.save()
            return redirect('evaluate_employees')
    
    context = {
        'assigned_employees': assigned_employees,
        'selected_employee': selected_employee,
        'evaluation_details_data': evaluation_details_data,
        'status_already_completed': status_already_completed,
    }
    return render(request, 'evaluations/evaluate_employees.html', context)

# Vista para mostrar gráfico radar de resumen de evaluaciones
@roles_required("Administrador", "Gerente", "Lider")
def radar_chart_summary(request):
    # Obtener todas las posiciones para el filtro
    positions = Position.objects.all()
    
    # Obtener todos los ciclos de evaluación únicos para el filtro
    evaluation_cycles = Permanent_EvaluationAssignment.objects.values_list('evaluation_cycle', flat=True).distinct()
    
    # Filtrar por posición si se proporcionó en la solicitud
    position_id = request.GET.get('position_id')
    
    # Filtrar por ciclo de evaluación si se proporcionó en la solicitud
    evaluation_cycle = request.GET.get('evaluation_cycle')
    
    # Aplicar filtros
    employee_query = Usuario.objects.all()
    
    # Aplicar filtro por posición si existe
    if position_id:
        employee_query = employee_query.filter(position_id=position_id)
    
    # Obtener los empleados según los filtros aplicados
    if evaluation_cycle:
        # Obtenemos los IDs de los empleados que tienen asignaciones en este ciclo
        assignment_filter = Permanent_EvaluationAssignment.objects.filter(
            evaluation_cycle=evaluation_cycle
        )
        employee_ids = assignment_filter.values_list('employee_id', flat=True).distinct()
        
        # Aplicamos el filtro adicional por empleados que tienen asignaciones en este ciclo
        employee_query = employee_query.filter(id__in=employee_ids)
        
    # Si no se seleccionó ningún ciclo, al menos filtramos por empleados que tengan alguna asignación
    else:
        # Obtenemos IDs de empleados con cualquier asignación permanente
        employee_ids = Permanent_EvaluationAssignment.objects.values_list('employee_id', flat=True).distinct()
        employee_query = employee_query.filter(id__in=employee_ids)
    
    # Obtener la lista final de empleados aplicando todos los filtros
    employees = employee_query
    
    # Obtener el empleado seleccionado si existe
    employee_id = request.GET.get('employee_id')
    employee_data = None
    
    if employee_id:
        try:
            # Obtener únicamente las asignaciones permanentes para el empleado seleccionado
            permanent_assignments_query = Permanent_EvaluationAssignment.objects.filter(
                employee_id=employee_id,
                summary__isnull=False
            )
            
            # Si hay un ciclo seleccionado, filtramos también por ese ciclo
            if evaluation_cycle:
                permanent_assignments_query = permanent_assignments_query.filter(evaluation_cycle=evaluation_cycle)
                
            permanent_assignments = permanent_assignments_query.order_by('evaluation_cycle')
            
            if permanent_assignments.exists():
                # Obtener información básica del empleado
                employee = Usuario.objects.get(id=employee_id)
                
                # Preparar los datos para el gráfico radar
                employee_data = {
                    'name': f"{employee.first_name} {employee.last_name}",
                    'position': employee.position.position_name,
                    'summaries': []
                }
                
                # Procesamos solamente las asignaciones permanentes
                for assignment in permanent_assignments:
                    summary = assignment.summary
                    if summary:
                        # Usar el ciclo de evaluación como etiqueta
                        cycle_label = assignment.evaluation_cycle
                        
                        # Agregar los datos de esta evaluación
                        employee_data['summaries'].append({
                            'created_at': cycle_label,  # Usamos evaluation_cycle en lugar de la fecha
                            'data': {
                                'R': summary.R,
                                'L': summary.L if summary.L is not None else 0,
                                'H': summary.H,
                                'E': summary.E,
                                'C': summary.C,
                                'M': summary.M,                                'V': summary.V
                            }
                        })
        except Usuario.DoesNotExist:
            pass
    
    context = {
        'positions': positions,
        'evaluation_cycles': evaluation_cycles,
        'employees': employees,
        'employee_data': employee_data,
        'selected_position_id': position_id,
        'selected_evaluation_cycle': evaluation_cycle,
        'selected_employee_id': employee_id
    }
    
    return render(request, 'System/radar_chart_summary.html', context)

# Vista para mostrar gráfico de barras comparativo de evaluaciones
@roles_required("Administrador", "Gerente", "Lider")
def bar_chart_comparison(request):
    # Obtener todos los ciclos de evaluación disponibles para el filtro
    evaluation_cycles = Permanent_EvaluationAssignment.objects.values_list('evaluation_cycle', flat=True).distinct()
    
    # Filtrar por ciclo de evaluación si se proporcionó en la solicitud
    cycle_id = request.GET.get('cycle_id')
    
    # Obtener los empleados relevantes según el ciclo seleccionado
    if cycle_id:
        # Obtener las asignaciones del ciclo seleccionado
        assignments = Permanent_EvaluationAssignment.objects.filter(evaluation_cycle=cycle_id, summary__isnull=False)
        # Obtener los empleados de esas asignaciones
        employee_ids = assignments.values_list('employee_id', flat=True).distinct()
        employees = Usuario.objects.filter(id__in=employee_ids)
    else:
        # Si no hay ciclo seleccionado, mostrar todos los empleados
        employees = Usuario.objects.all()
    
    # Obtener los empleados seleccionados (pueden ser múltiples)
    selected_employee_ids = request.GET.getlist('employee_ids')
    comparison_data = []
    
    if selected_employee_ids:
        for employee_id in selected_employee_ids:
            try:
                # Obtener el empleado
                employee = Usuario.objects.get(id=employee_id)
                
                # Obtener la asignación del ciclo seleccionado para este empleado
                if cycle_id:
                    assignment = Permanent_EvaluationAssignment.objects.filter(
                        employee_id=employee_id,
                        evaluation_cycle=cycle_id,
                        summary__isnull=False
                    ).first()
                else:
                    # Si no hay ciclo seleccionado, usar la asignación más reciente
                    assignment = Permanent_EvaluationAssignment.objects.filter(
                        employee_id=employee_id,
                        summary__isnull=False
                    ).order_by('-created_at').first()
                
                if assignment and assignment.summary:
                    # Preparar los datos para el gráfico usando el resumen de la asignación
                    summary = assignment.summary
                    employee_data = {
                        'id': employee.id,
                        'name': f"{employee.first_name} {employee.last_name}",
                        'position': employee.position.position_name,
                        'cycle': assignment.evaluation_cycle,
                        'data': {
                            'R': summary.R,
                            'L': summary.L if summary.L is not None else 0,
                            'H': summary.H,
                            'E': summary.E,
                            'C': summary.C,
                            'M': summary.M,
                            'V': summary.V
                        }
                    }
                    comparison_data.append(employee_data)
            except Usuario.DoesNotExist:
                pass
    
    context = {
        'evaluation_cycles': evaluation_cycles,
        'employees': employees,
        'comparison_data': comparison_data,
        'selected_cycle_id': cycle_id,
        'selected_employee_ids': selected_employee_ids
    }
    
    return render(request, 'System/bar_chart_comparison.html', context)

# Listar posiciones
@method_decorator(roles_required("Administrador"), name='dispatch')
class PositionListView(ListView):
    model = Position
    template_name = 'positions/position_list.html'
    context_object_name = 'positions'

# Ver detalle de una posición
@method_decorator(roles_required("Administrador"), name='dispatch')
class PositionDetailView(DetailView):
    model = Position
    template_name = 'positions/position_detail.html'
    context_object_name = 'position'

# Crear una nueva posición
@method_decorator(roles_required("Administrador"), name='dispatch')
class PositionCreateView(CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'positions/position_form.html'
    success_url = reverse_lazy('position_list')

# Actualizar una posición
@method_decorator(roles_required("Administrador"), name='dispatch')
class PositionUpdateView(UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'positions/position_form.html'
    context_object_name = 'position'
    success_url = reverse_lazy('position_list')

# Eliminar una posición
@method_decorator(roles_required("Administrador"), name='dispatch')
class PositionDeleteView(DeleteView):
    model = Position
    template_name = 'positions/position_confirm_delete.html'
    context_object_name = 'position'
    success_url = reverse_lazy('position_list')
    

# User_templates
@method_decorator(roles_required("Administrador"), name='dispatch')
class UserTemplateListView(ListView):
    model = Usuario
    template_name = 'users_templates/user_template_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        return Usuario.objects.exclude(user_type__in=['Administrador', 'Gerente']).select_related('template')

@method_decorator(roles_required("Administrador"), name='dispatch')
class UserTemplateAssignView(FormView):
    template_name = 'users_templates/user_template_assign.html'
    form_class = UserTemplateAssignForm 
    success_url = reverse_lazy('user_template_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = Usuario.objects.exclude(user_type__in=['Administrador', 'Gerente'])
        context['templates'] = Template.objects.all()
        return context

    def form_valid(self, form):
        user_id = form.cleaned_data['user_id'].id
        template_id = form.cleaned_data['template_id'].id
        try:
            user = Usuario.objects.get(id=user_id)
            template = Template.objects.get(id=template_id)
            user.template = template
            user.save()
        except (Usuario.DoesNotExist, Template.DoesNotExist):
            pass
        return super().form_valid(form)
    
@method_decorator(roles_required("Administrador"), name='dispatch')
class UserTemplateEditView(View):
    def get(self, request, user_id):
        # Obtén el usuario y su plantilla actual
        user = get_object_or_404(Usuario, id=user_id)
        form = UserTemplateEditForm(initial={
            'template_id': user.template.id if user.template else None  # Plantilla actual
        })
        return render(request, 'users_templates/user_template_edit.html', {'form': form, 'user': user})

    def post(self, request, user_id):
        # Obtén el usuario
        user = get_object_or_404(Usuario, id=user_id)
        form = UserTemplateEditForm(request.POST)  # Procesa los datos enviados
        if form.is_valid():
            # Actualiza la plantilla del usuario
            template = form.cleaned_data['template_id']
            user.template = template
            user.save()
            return redirect('user_template_list')  # Redirige a la lista de usuarios
        else:
            # Si el formulario no es válido, vuelve a renderizarlo con errores
            return render(request, 'users_templates/user_template_edit.html', {'form': form, 'user': user})
    
@method_decorator(roles_required("Administrador"), name='dispatch')
class UserTemplateUnassignView(DeleteView):
    model = Usuario
    success_url = reverse_lazy('user_template_list')

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.template = None
        user.save()
        return redirect(self.success_url)