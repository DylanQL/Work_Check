from django.shortcuts import render, redirect
from functools import wraps
from django.contrib import messages
from .models import *
from django.db import transaction


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
    user_id = request.session.get('user_id')
    user_account = UserAccount.objects.get(id=user_id)
    usuario = user_account.usuario
    return render(request, 'System/home.html', {'usuario': usuario})

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
        return redirect('list_temp_assignments')
    
    if request.method == 'POST':
        assignment.delete()
        return redirect('list_temp_assignments')
    
    return render(request, 'System/delete_temp_evaluation_assignment.html', {'assignment': assignment})

# Enviar registros a histórico:
@login_required
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

@login_required
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
    return render(request, 'System/employees_evaluations.html', {'assignments': assignments})


@login_required
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
        R1 = request.POST.get('R1', 0)
        R2 = request.POST.get('R2', 0)
        R3 = request.POST.get('R3', 0)
        R4 = request.POST.get('R4', 0)
        R5 = request.POST.get('R5', 0)
        R_comments = request.POST.get('R_comments', '')

        L1 = request.POST.get('L1', 0)
        L2 = request.POST.get('L2', 0)
        L3 = request.POST.get('L3', 0)
        L4 = request.POST.get('L4', 0)
        L5 = request.POST.get('L5', 0)
        L_comments = request.POST.get('L_comments', '')

        H1 = request.POST.get('H1', 0)
        H2 = request.POST.get('H2', 0)
        H3 = request.POST.get('H3', 0)
        H4 = request.POST.get('H4', 0)
        H5 = request.POST.get('H5', 0)
        H_comments = request.POST.get('H_comments', '')

        E1 = request.POST.get('E1', 0)
        E2 = request.POST.get('E2', 0)
        E3 = request.POST.get('E3', 0)
        E4 = request.POST.get('E4', 0)
        E_comments = request.POST.get('E_comments', '')

        C1 = request.POST.get('C1', 0)
        C2 = request.POST.get('C2', 0)
        C3 = request.POST.get('C3', 0)
        C4 = request.POST.get('C4', 0)
        C5 = request.POST.get('C5', 0)
        C6 = request.POST.get('C6', 0)
        C_comments = request.POST.get('C_comments', '')

        M1 = request.POST.get('M1', 0)
        M2 = request.POST.get('M2', 0)
        M_comments = request.POST.get('M_comments', '')

        V1 = request.POST.get('V1', 0)
        V2 = request.POST.get('V2', 0)
        V3 = request.POST.get('V3', 0)
        V4 = request.POST.get('V4', 0)
        V5 = request.POST.get('V5', 0)
        V_comments = request.POST.get('V_comments', '')

        final_comments = request.POST.get('final_comments', '')

        button_clicked = request.POST.get('action')

        if button_clicked == "Limpiar formulario":
            return redirect('evaluate_leaders')  # o la URL que quieras recargar

        # Si se hace clic en "Enviar formulario"
        if button_clicked == "Enviar formulario" and employee_id_post:
            # Se maneja la creación/actualización de EvaluationDetails y Summary
            with transaction.atomic():
                # 1. Crear/actualizar EvaluationDetails
                assignment = assignment_by_employee.get(employee_id_post)
                if not assignment:
                    # Error, no hay asignación
                    return redirect('evaluate_leaders')

                if assignment.evaluation_details:
                    # Actualizar
                    ed = assignment.evaluation_details
                else:
                    # Crear
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
                    vals = [int(v) for v in values]
                    return sum(vals)/len(vals) if len(vals) > 0 else 0

                R_avg = avg(R1, R2, R3, R4, R5)
                L_avg = avg(L1, L2, L3, L4, L5)
                H_avg = avg(H1, H2, H3, H4, H5)
                E_avg = avg(E1, E2, E3, E4)
                C_avg = avg(C1, C2, C3, C4, C5, C6)
                M_avg = avg(M1, M2)
                # V is a sum, not an average
                V_sum = sum([int(v) for v in [V1, V2, V3, V4, V5]])

                # Pesos
                w_R = 0.20
                w_L = 0.20
                w_H = 0.10
                w_E = 0.10
                w_C = 0.15
                w_M = 0.15
                w_V = 0.10

                R_weighted = R_avg * w_R
                L_weighted = L_avg * w_L
                H_weighted = H_avg * w_H
                E_weighted = E_avg * w_E
                C_weighted = C_avg * w_C
                M_weighted = M_avg * w_M
                # Apply weighting to the sum of V, not to an average
                V_weighted = V_sum * w_V

                final_score = R_weighted + L_weighted + H_weighted + E_weighted + C_weighted + M_weighted + V_weighted


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
    return render(request, 'System/evaluate_leaders.html', context)

@login_required
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
            # O alternativamente: Usuario.objects.get(id=selected_employee_id)
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
        except (ValueError, Exception):
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

        # Recoger todos los campos del formulario para EvaluationDetails
        R1 = request.POST.get('R1', 0)
        R2 = request.POST.get('R2', 0)
        R3 = request.POST.get('R3', 0)
        R4 = request.POST.get('R4', 0)
        R5 = request.POST.get('R5', 0)
        R_comments = request.POST.get('R_comments', '')

        H1 = request.POST.get('H1', 0)
        H2 = request.POST.get('H2', 0)
        H3 = request.POST.get('H3', 0)
        H4 = request.POST.get('H4', 0)
        H5 = request.POST.get('H5', 0)
        H_comments = request.POST.get('H_comments', '')

        E1 = request.POST.get('E1', 0)
        E2 = request.POST.get('E2', 0)
        E3 = request.POST.get('E3', 0)
        E4 = request.POST.get('E4', 0)
        E_comments = request.POST.get('E_comments', '')

        C1 = request.POST.get('C1', 0)
        C2 = request.POST.get('C2', 0)
        C3 = request.POST.get('C3', 0)
        C4 = request.POST.get('C4', 0)
        C5 = request.POST.get('C5', 0)
        C6 = request.POST.get('C6', 0)
        C_comments = request.POST.get('C_comments', '')

        M1 = request.POST.get('M1', 0)
        M2 = request.POST.get('M2', 0)
        M_comments = request.POST.get('M_comments', '')

        V1 = request.POST.get('V1', 0)
        V2 = request.POST.get('V2', 0)
        V3 = request.POST.get('V3', 0)
        V4 = request.POST.get('V4', 0)
        V5 = request.POST.get('V5', 0)
        V_comments = request.POST.get('V_comments', '')

        final_comments = request.POST.get('final_comments', '')

        button_clicked = request.POST.get('action')
        if button_clicked == "Limpiar formulario":
            return redirect('evaluate_employees')

        if button_clicked == "Enviar formulario" and employee_id_post:
            from django.db import transaction
            with transaction.atomic():
                assignment = assignment_by_employee.get(employee_id_post)
                if not assignment:
                    return redirect('evaluate_employees')
                # Crear o actualizar EvaluationDetails
                if assignment.evaluation_details:
                    ed = assignment.evaluation_details
                else:
                    from .models import EvaluationDetails
                    ed = EvaluationDetails()
                ed.R1 = R1; ed.R2 = R2; ed.R3 = R3; ed.R4 = R4; ed.R5 = R5; ed.R_comments = R_comments
                ed.H1 = H1; ed.H2 = H2; ed.H3 = H3; ed.H4 = H4; ed.H5 = H5; ed.H_comments = H_comments
                ed.E1 = E1; ed.E2 = E2; ed.E3 = E3; ed.E4 = E4; ed.E_comments = E_comments
                ed.C1 = C1; ed.C2 = C2; ed.C3 = C3; ed.C4 = C4; ed.C5 = C5; ed.C6 = C6; ed.C_comments = C_comments
                ed.M1 = M1; ed.M2 = M2; ed.M_comments = M_comments
                ed.V1 = V1; ed.V2 = V2; ed.V3 = V3; ed.V4 = V4; ed.V5 = V5; ed.V_comments = V_comments
                ed.final_comments = final_comments
                ed.save()
                assignment.evaluation_details = ed

                # Calcular promedios (conversión a float)
                def avg(*vals):
                    try:
                        numbers = [float(v) for v in vals]
                        return sum(numbers)/len(numbers) if numbers else 0
                    except:
                        return 0

                R_avg = avg(R1, R2, R3, R4, R5)
                H_avg = avg(H1, H2, H3, H4, H5)
                E_avg = avg(E1, E2, E3, E4)
                C_avg = avg(C1, C2, C3, C4, C5, C6)
                M_avg = avg(M1, M2)
                V_sum = sum([int(v) for v in [V1, V2, V3, V4, V5]])

                # Ponderados para empleados
                w_R = 0.40
                w_H = 0.10
                w_E = 0.10
                w_C = 0.15
                w_M = 0.15
                w_V = 0.10

                R_weighted = R_avg * w_R
                H_weighted = H_avg * w_H
                E_weighted = E_avg * w_E
                C_weighted = C_avg * w_C
                M_weighted = M_avg * w_M
                V_weighted = V_sum * w_V

                final_score = R_weighted + H_weighted + E_weighted + C_weighted + M_weighted + V_weighted

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


                # Crear o actualizar Summary
                if assignment.summary:
                    summ = assignment.summary
                else:
                    from .models import Summary
                    summ = Summary()
                summ.employee = assignment.employee
                summ.evaluator = assignment.evaluator
                summ.R = R_avg
                summ.H = H_avg
                summ.E = E_avg
                summ.C = C_avg
                summ.M = M_avg
                summ.V = V_sum
                summ.final_score = final_score
                summ.performance_level = performance_level
                summ.evaluation_type = "Empleados"
                summ.position = assignment.employee.position
                summ.save()

                assignment.summary = summ
                assignment.status = "Completado"
                assignment.save()

            return redirect('evaluate_employees')
    
    context = {
        'assigned_employees': assigned_employees,
        'selected_employee': selected_employee,
        'evaluation_details_data': evaluation_details_data,
        'status_already_completed': status_already_completed,
    }
    return render(request, 'System/evaluate_employees.html', context)

# Vista para mostrar gráfico radar de resumen de evaluaciones
@login_required
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
@login_required
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
