document.addEventListener('DOMContentLoaded', function() {
    
    const dropdownBotao = document.querySelector('.dropdown-botao-icone');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    if (dropdownBotao) {
        
        dropdownBotao.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('ativo');
        });

        window.addEventListener('click', function() {
            if (dropdownMenu.classList.contains('ativo')) {
                dropdownMenu.classList.remove('ativo');
            }
        });
    }
});


document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Encontra todos os botões que abrem um modal
    const modalTriggers = document.querySelectorAll('.js-modal-trigger');
    
    // 2. Encontra todos os botões que fecham um modal
    const modalCloses = document.querySelectorAll('.js-modal-close');

    // Adiciona o 'click' para cada botão que ABRE
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            // Pega o ID do modal alvo (ex: '#rejeitarModal-1')
            const targetSelector = trigger.getAttribute('data-target');
            const modal = document.querySelector(targetSelector);
            
            if (modal) {
                modal.classList.add('ativo');
            }
        });
    });

    // Adiciona o 'click' para cada botão que FECHA
    modalCloses.forEach(close => {
        close.addEventListener('click', () => {
            // Encontra o modal "pai" mais próximo e o fecha
            const modal = close.closest('.modal');
            if (modal) {
                modal.classList.remove('ativo');
            }
        });
    });

    // 3. Fecha o modal se o usuário clicar fora dele (no fundo escuro)
    window.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            e.target.classList.remove('ativo');
        }
    });

});