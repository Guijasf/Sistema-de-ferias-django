document.addEventListener('DOMContentLoaded', function() {
  var calendarioEl = document.getElementById('calendario');
  
  var calendario = new FullCalendar.Calendar(calendarioEl, {
    initialView: 'dayGridMonth',
    locale: 'pt-br',
    
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,listWeek'
    },
    
    fixedWeekCount: false, 
    height: 'auto',        
    events: '/api/eventos/',
    timeZone: 'local'
  });
  
  calendario.render();
});