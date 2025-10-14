// Aguarda o documento carregar completamente
document.addEventListener('DOMContentLoaded', function() {
  // Pega o elemento da div onde o calendário será renderizado
  var calendarioEl = document.getElementById('calendario');
  
  // Cria uma nova instância do FullCalendar
  var calendario = new FullCalendar.Calendar(calendarioEl, {
    // Visão inicial do calendário como um mês
    initialView: 'dayGridMonth',
    
    // Define o idioma para português do Brasil
    locale: 'pt-br',
    
    // Botões no cabeçalho (anterior, próximo, hoje)
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,listWeek'
    },
    
    // O calendário vai buscar os eventos na nossa API que criamos!
    events: '/api/eventos/',
    
    // Ajusta o fuso horário para não ter problemas com datas
    timeZone: 'local'
  });
  
  // Renderiza o calendário na tela
  calendario.render();
});