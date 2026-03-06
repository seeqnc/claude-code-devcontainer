"Builtin
set wrap
set tabstop=4
set shiftwidth=4
" set expandtab
set autoindent
set smartindent
set wildchar=<Tab>
set nonumber
set foldmethod=marker
set hidden
set wmh=0
set bg=dark
"set textwidth=120


" Ermöglicht das Navigieren zwischen split Fenstern
" horizontal und vertikal
nmap <C-J> <C-W>j<C-W>_
nmap <C-K> <C-W>k<C-W>_
nmap <c-h> <c-w>h<c-w><bar>
nmap <c-l> <c-w>l<c-w><bar>

" Arbeiten in Terminalfenstern mit dunklem und hellem Hintergrund
" einfach umschalten mit F11 und F12
map <F10> :set bg=light<CR>
map <F9> :set bg=dark<CR>

" Esc ist soo weit weg - daher umschalten in Kommandomodus mit Shift-Leertaste
imap <S-Space> <Esc>

"Extras
"winmanager
"map <F2> :set pastetoggle<CR>
"taglist
map <F3> :Tlist<CR>

nnoremap <F2> :set invpaste paste?<CR>
nnoremap <F5> :set listchars=eol:¬,tab:>·,trail:~,extends:>,precedes:<,space:␣ list!<CR>
set pastetoggle=<F2>
set showmode

"call togglebg#map("<F5>")

autocmd BufRead *.vala,*.vapi set efm=%f:%l.%c-%[%^:]%#:\ %t%[%^:]%#:\ %m
autocmd Filetype yaml,yml setlocal ts=2 sw=2 expandtab
au BufRead,BufNewFile *.vala,*.vapi setfiletype vala

au BufRead,BufNewFile *.logstash setfiletype logstash

execute pathogen#infect()
"let g:solarized_termcolors=256
let g:solarized_termtrans=1
colorscheme solarized

filetype off

set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

" Utility
Plugin 'Matt-Deacalion/vim-systemd-syntax'
Plugin 'bracki/vim-prometheus'
Plugin 'scrooloose/nerdtree'
Plugin 'majutsushi/tagbar'
Plugin 'ervandew/supertab'
"Plugin 'BufOnly.vim'
"Plugin 'wesQ3/vim-windowswap'
Plugin 'SirVer/ultisnips'
"Plugin 'junegunn/fzf.vim'
"Plugin 'junegunn/fzf'
"Plugin 'godlygeek/tabular'
"Plugin 'ctrlpvim/ctrlp.vim'
"Plugin 'benmills/vimux'
"Plugin 'jeetsukumaran/vim-buffergator'
"Plugin 'gilsondev/searchtasks.vim'
" Plugin 'Shougo/neocomplete.vim'
if has('nvim')
  Plugin 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }
else
  Plugin 'Shougo/deoplete.nvim'
  Plugin 'roxma/nvim-yarp'
  Plugin 'roxma/vim-hug-neovim-rpc'
endif 
Plugin 'tpope/vim-dispatch'
Plugin 'jceb/vim-orgmode'
Plugin 'tpope/vim-speeddating'

" Generic Programming Support 
Plugin 'jakedouglas/exuberant-ctags'
Plugin 'honza/vim-snippets'
Plugin 'Townk/vim-autoclose'
Plugin 'tomtom/tcomment_vim'
Plugin 'tobyS/vmustache'
Plugin 'maksimr/vim-jsbeautify'
Plugin 'vim-syntastic/syntastic'

" Markdown / Writting
Plugin 'reedes/vim-pencil'
Plugin 'tpope/vim-markdown'
Plugin 'jtratner/vim-flavored-markdown'
"Plugin 'LanguageTool'

" Git Support
Plugin 'kablamo/vim-git-log'
Plugin 'gregsexton/gitv'
Plugin 'tpope/vim-fugitive'

" jsonnet
Plugin 'google/vim-jsonnet'

" toml
Plugin 'cespare/vim-toml'


call vundle#end()            " required
filetype plugin indent on
syntax on

let g:vim_json_syntax_conceal = 0

" Vim-Airline Configuration
let g:airline#extensions#tabline#enabled = 1
let g:airline_powerline_fonts = 1 
let g:airline_theme='hybrid'
let g:hybrid_custom_term_colors = 1
let g:hybrid_reduced_contrast = 1 

" Syntastic Configuration
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 1
let g:syntastic_check_on_open = 1
" let g:syntastic_check_on_wq = 0
" let g:syntastic_enable_elixir_checker = 1
" let g:syntastic_elixir_checkers = ["elixir"]
" let g:syntastic_ruby_checkers = ["rubocop"]

" Markdown Syntax Support
augroup markdown
    au!
    au BufNewFile,BufRead *.md,*.markdown setlocal filetype=ghmarkdown
augroup END

"""""""""""""""""""""""""""""""""""""
" Mappings configurationn
"""""""""""""""""""""""""""""""""""""
map <C-n> :NERDTreeToggle<CR>
map <C-m> :TagbarToggle<CR>

" Omnicomplete Better Nav
inoremap <expr> <c-j> ("\<C-n>")
inoremap <expr> <c-k> ("\<C-p>")

" Neocomplete Plugin mappins
inoremap <expr><C-g>     neocomplete#undo_completion()
inoremap <expr><C-l>     neocomplete#complete_common_string()

" Recommended key-mappings.
" <CR>: close popup and save indent.
"inoremap <silent> <CR> <C-r>=<SID>my_cr_function()<CR>

" <TAB>: completion.
inoremap <expr><TAB>  pumvisible() ? "\<C-n>" : "\<TAB>"

" <C-h>, <BS>: close popup and delete backword char.
" inoremap <expr><C-h> neocomplete#smart_close_popup()."\<C-h>"
" inoremap <expr><BS> neocomplete#smart_close_popup()."\<C-h>"

" Mapping selecting Mappings
nmap <leader><tab> <plug>(fzf-maps-n)
xmap <leader><tab> <plug>(fzf-maps-x)
omap <leader><tab> <plug>(fzf-maps-o)

" Shortcuts
nnoremap <Leader>o :Files<CR> 
nnoremap <Leader>O :CtrlP<CR>
nnoremap <Leader>w :w<CR>

" Insert mode completion
imap <c-x><c-k> <plug>(fzf-complete-word)
imap <c-x><c-f> <plug>(fzf-complete-path)
imap <c-x><c-j> <plug>(fzf-complete-file-ag)
imap <c-x><c-l> <plug>(fzf-complete-line)

au BufNewFile postmortem-*.md 0r ~/Projects/braintribe/tfcloud-postmortems/postmortem-template.md

