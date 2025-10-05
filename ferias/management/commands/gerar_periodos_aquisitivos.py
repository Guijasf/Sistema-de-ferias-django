import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from ferias.models import Funcionario, PeriodoAquisitivo

class Command(BaseCommand):
    help = 'Verifica e gera novos períodos aquisitivos para funcionários que completaram mais um ano de serviço.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando verificação de períodos aquisitivos...'))
        
        hoje = timezone.now().date()
        funcionarios = Funcionario.objects.all()
        
        for funcionario in funcionarios:
            data_nomeacao = funcionario.data_nomeacao
            
            ultimo_periodo = funcionario.periodos_aquisitivos.order_by('-data_inicio').first()
            
            if ultimo_periodo:
                proximo_aniversario = ultimo_periodo.data_inicio + relativedelta(years=1)
            else:
                proximo_aniversario = data_nomeacao

            while proximo_aniversario <= hoje:
                data_inicio_novo_periodo = proximo_aniversario
                data_fim_novo_periodo = data_inicio_novo_periodo + relativedelta(years=1) - datetime.timedelta(days=1)
                

                ja_existe = PeriodoAquisitivo.objects.filter(
                    funcionario=funcionario,
                    data_inicio=data_inicio_novo_periodo
                ).exists()
                
                if not ja_existe:
                    PeriodoAquisitivo.objects.create(
                        funcionario=funcionario,
                        data_inicio=data_inicio_novo_periodo,
                        data_fim=data_fim_novo_periodo,
                        saldo_dias=30.00
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'Novo período aquisitivo {data_inicio_novo_periodo.year}/{data_fim_novo_periodo.year} '
                        f'criado para {funcionario.user.username}.'
                    ))
                
                proximo_aniversario += relativedelta(years=1)

        self.stdout.write(self.style.SUCCESS('Verificação concluída.'))