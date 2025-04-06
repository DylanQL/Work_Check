from django.db import models

# Create your models here.
class Position(models.Model):
    position_code = models.CharField(max_length=20)
    position_name = models.CharField(max_length=100)


class Usuario(models.Model):
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50)
    second_last_name = models.CharField(max_length=50, blank=True, null=True)
    user_type = models.CharField(max_length=50)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)

class TimeSheetScore(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    score_ts = models.IntegerField()

class EvaluationDetails(models.Model):
    # Responsabilidades de la posición
    R1 = models.IntegerField()
    R2 = models.IntegerField()
    R3 = models.IntegerField()
    R4 = models.IntegerField()
    R5 = models.IntegerField()
    R_comments = models.TextField(blank=True, null=True)
    
    # Responsabilidades por liderazgo
    L1 = models.IntegerField(blank=True, null=True)
    L2 = models.IntegerField(blank=True, null=True)
    L3 = models.IntegerField(blank=True, null=True)
    L4 = models.IntegerField(blank=True, null=True)
    L5 = models.IntegerField(blank=True, null=True)
    L_comments = models.TextField(blank=True, null=True)
    
    # Habilidades
    H1 = models.IntegerField()
    H2 = models.IntegerField()
    H3 = models.IntegerField()
    H4 = models.IntegerField()
    H5 = models.IntegerField()
    H_comments = models.TextField(blank=True, null=True)
    
    # Enfoque
    E1 = models.IntegerField()
    E2 = models.IntegerField()
    E3 = models.IntegerField()
    E4 = models.IntegerField()
    E_comments = models.TextField(blank=True, null=True)
    
    # Competencia Técnica
    C1 = models.IntegerField()
    C2 = models.IntegerField()
    C3 = models.IntegerField()
    C4 = models.IntegerField()
    C5 = models.IntegerField()
    C6 = models.IntegerField()
    C_comments = models.TextField(blank=True, null=True)
    
    # Metas y Resultados
    M1 = models.IntegerField()
    M2 = models.IntegerField()
    M_comments = models.TextField(blank=True, null=True)
    
    # Valores Corporativos
    V1 = models.IntegerField()
    V2 = models.IntegerField()
    V3 = models.IntegerField()
    V4 = models.IntegerField()
    V5 = models.IntegerField()
    V_comments = models.TextField(blank=True, null=True)
    
    final_comments = models.TextField(blank=True, null=True)

class Summary(models.Model):

    employee = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='employee_summaries')
    evaluator = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='evaluator_summaries')
    R = models.FloatField() # Ponderado Responsabilidades de la posición
    L = models.FloatField(blank=True, null=True) # Ponderado Responsabilidades por liderazgo
    H = models.FloatField() # Ponderado Habilidades
    E = models.FloatField() # Ponderado Enfoque
    C = models.FloatField() # Ponderado Competencia Técnica
    M = models.FloatField() # Ponderado Metas y Resultados
    V = models.FloatField() # Ponderado Valores Corporativos
    final_score = models.FloatField() # Suma de ponderados
    performance_level = models.CharField(max_length=50)
    evaluation_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    evaluation_details = models.ForeignKey(EvaluationDetails, on_delete=models.CASCADE, null=True, blank=True)

class Temp_EvaluationAssignment(models.Model):
    evaluator = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='temp_evaluator_assignments')
    employee = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='temp_employee_assignments')
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, null=True, blank=True)
    evaluation_cycle = models.CharField(max_length=50)

class Permanent_EvaluationAssignment(models.Model):
    evaluator = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='permanent_evaluator_assignments')
    employee = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='permanent_employee_assignments')
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, null=True, blank=True)
    evaluation_cycle = models.CharField(max_length=50)

class UserAccount(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Esto luego lo encriptaremos
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    status = models.CharField(max_length=20)

class EvaluationCycle(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)