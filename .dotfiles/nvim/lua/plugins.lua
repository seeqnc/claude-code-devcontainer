return {
	-- Treesitter: syntax highlighting + text objects
	-- Parsers are pre-compiled during Docker build; no runtime install needed.
	{
		"nvim-treesitter/nvim-treesitter",
		lazy = false,
	},

	-- Telescope: fuzzy finder
	{
		"nvim-telescope/telescope.nvim",
		dependencies = { "nvim-lua/plenary.nvim" },
		keys = {
			{ "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "Find files" },
			{ "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "Live grep" },
			{ "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "Buffers" },
			{ "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "Help tags" },
		},
	},

	-- Git
	{ "tpope/vim-fugitive" },

	-- Commenting
	{
		"numToStr/Comment.nvim",
		config = function()
			require("Comment").setup()
		end,
	},

	-- Completion engine (required by minuet-ai)
	{
		"hrsh7th/nvim-cmp",
		dependencies = {
			"hrsh7th/cmp-buffer",
			"hrsh7th/cmp-path",
			"hrsh7th/cmp-nvim-lsp",
		},
		config = function()
			local cmp = require("cmp")
			cmp.setup({
				sources = cmp.config.sources({
					{ name = "nvim_lsp" },
					{ name = "minuet" },
					{ name = "path" },
				}, {
					{ name = "buffer" },
				}),
				mapping = cmp.mapping.preset.insert({
					["<C-Space>"] = cmp.mapping.complete(),
					["<CR>"] = cmp.mapping.confirm({ select = false }),
					["<C-e>"] = cmp.mapping.abort(),
					["<Tab>"] = cmp.mapping(function(fallback)
						if cmp.visible() then
							cmp.select_next_item()
						else
							fallback()
						end
					end, { "i", "s" }),
					["<S-Tab>"] = cmp.mapping(function(fallback)
						if cmp.visible() then
							cmp.select_prev_item()
						else
							fallback()
						end
					end, { "i", "s" }),
				}),
				performance = {
					debounce = 100,
				},
			})
		end,
	},

	-- Codex ghost-text autocomplete
	{
		"milanglacier/minuet-ai.nvim",
		dependencies = { "nvim-lua/plenary.nvim" },
		config = function()
			local minuet_provider = vim.env.MINUET_PROVIDER or "openai"

			local key_env = minuet_provider == "claude" and "ANTHROPIC_API_KEY" or "OPENAI_API_KEY"
			if not os.getenv(key_env) then
				vim.schedule(function()
					vim.notify(
						"minuet-ai: set " .. key_env .. " for provider '" .. minuet_provider .. "'",
						vim.log.levels.WARN
					)
				end)
				return
			end

			require("minuet").setup({
				provider = minuet_provider,
				provider_options = {
					claude = {
						api_key = "ANTHROPIC_API_KEY",
						model = vim.env.MINUET_CLAUDE_MODEL or "claude-sonnet-4-20250514",
					},
					openai = {
						api_key = "OPENAI_API_KEY",
						model = vim.env.MINUET_OPENAI_MODEL or "gpt-5.4",
                        end_point = "https://sqnc-claude-foundry.openai.azure.com/openai/v1/chat/completions",
					},
				},
			})
		end,
	},

	-- LSP (data-only; configs come from nvim-lspconfig's lsp/ directory)
	{
		"neovim/nvim-lspconfig",
		config = function()
			local capabilities = vim.lsp.protocol.make_client_capabilities()
			local cmp_ok, cmp_lsp = pcall(require, "cmp_nvim_lsp")
			if cmp_ok then
				capabilities = cmp_lsp.default_capabilities(capabilities)
			end

			local servers = { "basedpyright", "ruff", "ts_ls" }
			for _, server in ipairs(servers) do
				vim.lsp.config(server, { capabilities = capabilities })
			end
			vim.lsp.enable(servers)

			vim.diagnostic.config({
				virtual_text = {
					severity = { min = vim.diagnostic.severity.ERROR },
				},
				signs = true,
				underline = true,
				update_in_insert = false,
				severity_sort = true,
				float = {
					source = "if_many",
					border = "rounded",
				},
			})

			local diagnostics_enabled = true
			vim.keymap.set("n", "<leader>td", function()
				diagnostics_enabled = not diagnostics_enabled
				vim.diagnostic.enable(diagnostics_enabled)
				local state = diagnostics_enabled and "enabled" or "disabled"
				local level = diagnostics_enabled and vim.log.levels.INFO or vim.log.levels.WARN
				vim.notify("Diagnostics " .. state, level)
			end, { desc = "Toggle diagnostics" })

			vim.api.nvim_create_autocmd("LspAttach", {
				callback = function(args)
					local buf = args.buf
					local map = function(keys, fn, desc)
						vim.keymap.set("n", keys, fn, { buffer = buf, desc = desc })
					end
					map("gd", vim.lsp.buf.definition, "Go to definition")
					map("gr", vim.lsp.buf.references, "References")
					map("gl", vim.diagnostic.open_float, "Diagnostics")
					map("K", vim.lsp.buf.hover, "Hover")
					map("<leader>rn", vim.lsp.buf.rename, "Rename")
					map("<leader>ca", vim.lsp.buf.code_action, "Code action")
				end,
			})
		end,
	},

	-- Formatting
	{
		"stevearc/conform.nvim",
		config = function()
			require("conform").setup({
				formatters_by_ft = {
					python = { "ruff_format" },
					typescript = { "deno_fmt", "prettier", stop_after_first = true },
					typescriptreact = { "deno_fmt", "prettier", stop_after_first = true },
					javascript = { "deno_fmt", "prettier", stop_after_first = true },
					javascriptreact = { "deno_fmt", "prettier", stop_after_first = true },
					json = { "deno_fmt", "prettier", stop_after_first = true },
					yaml = { "prettier" },
					sh = { "shfmt" },
					bash = { "shfmt" },
				},
			})
		end,
	},

	-- Claude Code IDE bridge
	{
		"coder/claudecode.nvim",
		config = function()
			require("claudecode").setup()
		end,
	},
}
