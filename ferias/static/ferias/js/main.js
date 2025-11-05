// ferias/static/ferias/js/main.js

/*
 * Função para controlar o Dropdown do Menu de Usuário
 */
document.addEventListener('DOMContentLoaded', function() {
    
    const dropdownBotao = document.querySelector('.dropdown-botao');
    const dropdownMenu = document.querySelector('.dropdown-menu');

    // Se não encontrarmos o botão (ex: na tela de login), não faz nada.
    if (dropdownBotao) {
        
        // 1. Ação de clicar no botão
        dropdownBotao.addEventListener('click', function(e) {
            e.stopPropagation(); // Impede que o clique "vaze" para a janela
            // A mágica é aqui: "toggle" adiciona a classe se ela não existe,
            // e remove se ela já existe.
            dropdownMenu.classList.toggle('ativo');
        });

        // 2. Ação de clicar em qualquer lugar fora do menu
        window.addEventListener('click', function() {
            // Se o menu estiver ativo, remove a classe para fechá-lo
            if (dropdownMenu.classList.contains('ativo')) {
                dropdownMenu.classList.remove('ativo');
            }
        });
    }
});