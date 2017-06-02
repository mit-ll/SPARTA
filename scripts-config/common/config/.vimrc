" DICTIONARY SETTINGS
set dictionary=/usr/share/dict/words
set complete=k

" TAB/SPACE SETTINGS
set tabstop=2
set shiftwidth=2
set expandtab
" auto indent depending on filetype
filetype indent on
set ai

" SYNTACTICAL PROCESSING
syntax on
" SCons syntax highlighting
autocmd BufRead,BufNewFile SConscript set filetype=python
autocmd BufRead,BufNewFile SConstruct set filetype=python
" show bracket matches
set sm

" MISCELLANEOUS
" enforce text width with gq on highlighted area
set textwidth=80
" highlight searches
set hls
" case-insensitive searches
" set ignorecase
" turn on line numbering
set nu
" allow . to execute once for each line in a visual selection
vnoremap . :normal .<CR>
" saves 50 lines of command history
" set history=50

" SAVED MACROS
" remove all trailing whitespace
let @w = ':%s/\s\+$//'
" command! Killws :%s/\s\+$//g

" STUFF TO TRY
" set nocompatible " vim settings instead of vi settings
" set guifont=Luxi\ Mono\ 9
" set smarttab " backspace back up tab stops?
" set backspace=indent,eol,start " backspace works over more stuff?
" set shortmess+=A " don't show .swp warning messages
" set ruler " always show cursor position
" set noshowcmd " display incompelte commands
" set incsearch " incremental searching
" set hidden "allow hidden buffers
" set wrap
" set linebreak
" set showmatch " show matching brackets
" set wildmode=longest,list " makes tab completion work?
" set updatecount=0 " disables swap files
" set writebackup " next two have to go together...
" set nobackup
" filetype plugin indent on
" filetype plugin on
" command! flow :setlocal textwidth=0 wrap lbr nolist
" Other stuff from odain's vimrc
