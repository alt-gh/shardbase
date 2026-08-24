# ShardBase Foundation Roadmap Workbook

document_purpose: Working template for defining, reviewing, and completing the ShardBase foundation stage.
document_role: Planning and brainstorming document; not an architectural authority.
recommended_repository_path: app/Docs/ShardBase - Foundation Roadmap Workbook.md
current_stage: foundation
roadmap_status: approved for exploration and execution
working_method: Fill in each value after the colon. Use additional indented lines or bullets when a value needs more detail.
completion_rule: A topic is not complete merely because it has text; its value should be reviewed and deliberately accepted, revised, or deferred.

---

## 1. Existing Foundation Snapshot

project_name: ShardBase
current_definition: A privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.
current_goal: Let a knowledge base grow without losing lineage, portability, readability, or control.
product_identity_status: accepted
structural_model: Pool → Core → Shard → Pebble
primary_agent: Shard
architectural_source_of_truth: app/Docs/Shard - System Specification.md
database_local_authority: Each database's root-level Database.md
repository_default: Framework material is committed; local live databases and Inbox contents are ignored by default.
foundation_priority: Establish architecture and agent contracts before locking in implementation-specific requirements.
foundation_workbook_status: working
foundation_roadmap_status: approved
foundation_completion_status: incomplete

---

## 2. Foundation Stage — Core Questions

### Product Identity

what_is_shardbase:
  - ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to become a personal digital brain and source of truth.
  - ShardBase targets Obsidian as its primary knowledge environment while keeping its core data in human-readable Markdown and YAML so it remains readable and editable independently of Obsidian.
  - ShardBase organizes knowledge through metadata, relationships, links, search, views, and AI-assisted interaction rather than requiring users to navigate their knowledge primarily through folder structures.
  - ShardBase-created notes are designed to form an interconnected web of information through structural and semantic YAML metadata, document content, wikilinks, and compatible visualization and query tools.
  - Dataview is a primary and canonical interface for interacting with ShardBase data in Obsidian, but the underlying database must never depend on Dataview for its meaning or structural integrity.
  - ShardBase may use scripts and other tooling to provide additional functionality, but its core knowledge must remain understandable without those tools.
  - ShardBase can support multiple AI agents, with Shard serving as its canonical primary architectural and database agent.
  - ShardBase is modular and extensible. Users can add databases, notes, relationships, views, and functionality over time, allowing their ShardBase vault to grow alongside them across many subjects and areas of life.
  - Privacy is an explicit ShardBase design objective rather than merely a side effect of local Markdown storage.
  - The user owns and controls their core data. ShardBase should not require that data to leave the user's local environment.
  - External synchronization, backup, cloud storage, publishing, or sharing services such as iCloud or Obsidian Sync are choices made by the user and are separate from ShardBase's core operation.
  - ShardBase should eventually understand the intended visibility of information so private knowledge can remain private while information deliberately intended for sharing can be identified and handled appropriately. The exact universal `visibility` model remains a Foundation architectural question.
  - ShardBase can be compared to a private, personal Wikipedia as an explanatory analogy: an interconnected body of knowledge belonging to one user.
  - ShardBase's broader long-term vision is to become a user-owned digital brain: a growing, interconnected and AI-assisted source of truth that remains under the user's control.

what_is_shardbase_in_one_sentence: 
  - ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth.

what_is_shardbase_in_one_paragraph: 
  - ShardBase is a privacy-focused, user-owned structured Markdown knowledge-base framework designed to grow into an interconnected personal digital brain and source of truth. It uses human-readable Markdown and YAML to organize knowledge through explicit structure, metadata, relationships, links, search, views, and AI-assisted interaction while keeping the underlying information understandable and editable independently of any single tool. ShardBase targets Obsidian as its primary knowledge environment, supports modular databases and extensible tooling, and is designed to let a user's knowledge grow across many areas of life without sacrificing readability, portability, structural integrity, privacy, or control.

what_is_shardbase_not:
  - ShardBase is not a proprietary knowledge platform that owns, obscures, or locks away the user's core data.
  - ShardBase is not a cloud service and does not require cloud storage, synchronization, or an internet connection for the meaning or integrity of its core knowledge.
  - ShardBase is not an Obsidian-only data format. Obsidian is the primary target environment, but ShardBase knowledge must remain understandable and editable as ordinary Markdown and YAML outside Obsidian.
  - ShardBase is not merely a folder hierarchy, tagging convention, collection of templates, Dataview dashboard, or set of scripts. Those tools may participate in ShardBase, but none of them individually defines the framework.
  - ShardBase is not a traditional opaque database that requires specialized software to inspect or understand its underlying knowledge.
  - ShardBase is not designed to maximize structure, metadata, files, or automation. It should use the minimum structure necessary to preserve useful organization, relationships, growth, and integrity.
  - ShardBase is not an autonomous system that replaces human judgment or control. AI agents and automation may assist with organization, classification, retrieval, maintenance, and growth, but the user's knowledge and consequential decisions remain under user control.
  - ShardBase is not a single-purpose database or knowledge domain. It is a framework capable of supporting multiple modular databases across different subjects and areas of life.
  - ShardBase is not intended to silently rewrite, reorganize, publish, synchronize, or destroy user-owned knowledge.
  - ShardBase is not defined by any particular AI provider, synchronization service, plugin, query engine, scripting language, or future implementation technology.

why_does_shardbase_exist:
  - ShardBase exists because personal knowledge becomes more valuable as it accumulates, connects, and remains usable over time, but that value should not require surrendering ownership, privacy, readability, or control.
  - It exists to give users a durable foundation for building a personal source of truth that can grow across many subjects and areas of life without becoming trapped inside a particular application, service, AI provider, or proprietary format.
  - ShardBase is built on the belief that a person's knowledge should remain fundamentally theirs: understandable by humans, useful to software and AI, portable between tools, and available even when optional services or automation are unavailable.
  - It exists to make structured, interconnected knowledge sustainable over the long term by providing enough shared architecture for information to grow coherently without requiring excessive hierarchy, rigid organization, or dependence on hidden systems.
  - Its long-term purpose is to help a user's accumulated knowledge become an increasingly useful personal digital brain: a private, inspectable, interconnected body of information that can support memory, understanding, discovery, decision-making, and future AI-assisted interaction while remaining under the user's control.

core_problem_shardbase_solves:
  - The core problem ShardBase solves is that personal knowledge becomes increasingly difficult to keep coherent, connected, understandable, and useful as it grows.
  - Without a durable structural model, accumulated knowledge can gradually lose clear relationships, lineage, context, and consistent organization, making it harder for both humans and software to understand how information belongs together.
  - Existing organizational methods can work well at smaller scales but often force users to choose between loose flexibility and rigid structure, or require increasing amounts of manual organization to keep a growing knowledge base usable.
  - ShardBase addresses this problem by giving knowledge enough explicit, shared structure to grow as an interconnected system while preserving human readability, machine interpretability, portability, privacy, and user control.

secondary_problems_shardbase_solves:
  - Knowledge fragmentation: related information can become scattered across notes, folders, tags, applications, or organizational schemes without a durable way to express how it belongs together.
  - Loss of lineage and context: as information is subdivided and reorganized, it can become unclear which larger subject it belongs to, what its immediate relationship is, or how it fits into the broader knowledge base.
  - Inconsistent organization: independently created notes, metadata, naming conventions, and structures can drift over time, making the knowledge base harder to understand, maintain, query, and extend consistently.
  - Retrieval and discovery difficulty: accumulated knowledge may exist without being easy to find, navigate, reconnect, or surface through meaningful relationships and queries.
  - Tension between flexibility and structure: lightweight organizational approaches can become difficult to scale, while rigid systems can impose more hierarchy or maintenance than the information actually requires.
  - Tool and format dependence: knowledge can become overly dependent on a particular application, plugin, query system, service, or proprietary representation, reducing its portability and long-term durability.
  - Limited machine interpretability: loosely structured knowledge can be difficult for scripts, queries, automation, and AI agents to interpret reliably without guessing relationships, ownership, or intent.
  - Increasing maintenance burden: as a knowledge base grows, preserving naming, metadata, relationships, integrity, and organizational conventions can require increasing amounts of repetitive manual work.
  - Premature or excessive structure: attempts to keep information organized can create unnecessary files, hierarchy, metadata, or fragmentation that make the knowledge base more complicated rather than more useful.
  - Reduced user control: systems that hide structure, automate consequential changes, or depend on external services can make it harder for users to inspect, understand, move, or safely change their own knowledge.

what_is_currently_difficult_without_shardbase:
  - Keeping a growing collection of notes organized without continually redesigning folders, tags, naming conventions, metadata, or other organizational systems.
  - Knowing where new information belongs and deciding whether it should become a separate note, remain inside an existing note, or relate to several areas at once.
  - Preserving clear lineage and context as information is broken into smaller pieces, moved, renamed, expanded, or reorganized over time.
  - Maintaining consistent metadata, relationships, naming, and organizational conventions across a large and evolving knowledge base.
  - Finding relevant information again when the user remembers the subject or relationship but not the exact filename, folder, tag, or location where it was stored.
  - Understanding how pieces of knowledge connect across subjects without manually reconstructing those relationships from folders, tags, backlinks, or memory.
  - Creating useful queries, views, and automation when the underlying notes do not share predictable structure or metadata.
  - Giving AI agents and other software enough reliable context to understand ownership, relationships, hierarchy, and intent without forcing them to guess from filenames, prose, or inconsistent metadata.
  - Refactoring or reorganizing accumulated knowledge confidently without risking broken relationships, lost context, duplicated information, or accidental destruction of user-authored content.
  - Keeping the knowledge base portable and understandable when particular plugins, applications, synchronization services, automation, or AI tools are unavailable.
  - Avoiding the opposite failure mode of over-engineering the knowledge base with excessive folders, metadata, files, or hierarchy simply to keep it manageable.
  - Maintaining a coherent personal source of truth across many subjects and areas of life without the organizational burden growing faster than the usefulness of the knowledge itself.

what_should_become_easier_with_shardbase:
  - Capturing and adding new information without needing to redesign the knowledge base each time it grows.
  - Deciding where information belongs by using a shared model for database ownership, Pool membership, Core lineage, immediate parent, and whether the information should become a Core, Shard, Pebble, or remain ordinary content.
  - Growing existing knowledge naturally from simple notes into richer interconnected structures without requiring large up-front organizational decisions.
  - Understanding how information relates by preserving explicit lineage, metadata, links, and semantic relationships that can be inspected by both humans and software.
  - Finding and rediscovering knowledge through relationships, metadata, search, queries, links, and views rather than depending primarily on remembering filenames or folder locations.
  - Maintaining consistent structure, metadata, naming, and relationships as the knowledge base expands across many subjects and databases.
  - Querying, filtering, visualizing, and navigating accumulated knowledge because structurally similar information follows predictable conventions.
  - Giving AI agents and automation reliable context so they can assist with classification, retrieval, organization, validation, maintenance, and growth without repeatedly reconstructing the architecture from scratch.
  - Reviewing, validating, refactoring, and reorganizing knowledge with greater confidence because structural expectations and relationships are explicit and inspectable.
  - Moving between manual editing, Obsidian, Dataview, scripts, AI assistance, and future tooling without changing the fundamental meaning of the underlying knowledge.
  - Keeping the knowledge base understandable and useful even when optional views, plugins, automation, synchronization services, or AI assistance are unavailable.
  - Expanding ShardBase into new subjects and areas of life without every new database requiring an entirely new organizational philosophy.
  - Spending less effort maintaining the knowledge-management system itself and more effort using, connecting, understanding, and building upon the knowledge it contains.

what_should_remain_intentionally_manual_or_human_controlled:
  - The user should retain final authority over what knowledge belongs in ShardBase and what information they choose to capture, retain, archive, delete, publish, share, or keep private.
  - Consequential destructive actions such as deleting user-authored knowledge, permanently removing attachments, or performing irreversible transformations should require explicit user authorization.
  - Significant structural changes that alter the intended meaning, ownership, lineage, or organization of existing knowledge should remain subject to user review or explicit approval rather than occurring silently.
  - Changes to universal ShardBase architecture, database-local schemas, major conventions, or other contracts that affect how existing knowledge is interpreted should remain deliberate human-approved decisions.
  - The user should control whether and when private information leaves the local environment, including its use with external AI providers, cloud services, synchronization systems, publishing systems, or other third-party services.
  - Decisions about the intended visibility and sharing of knowledge should ultimately belong to the user, even if ShardBase later assists with identifying, classifying, or enforcing visibility rules.
  - AI agents and automation may recommend classifications, relationships, metadata, restructuring, or maintenance actions, but they should expose consequential assumptions and preserve a meaningful path for user review, correction, or rejection.
  - Ambiguous decisions involving personal meaning, subjective judgment, competing interpretations, or unclear ownership should not be silently resolved by automation when the choice could materially affect the user's knowledge.
  - ShardBase should automate repetitive, deterministic, and safely reversible work where appropriate while keeping consequential, ambiguous, privacy-sensitive, or destructive decisions under meaningful human control.

why_is_markdown_the_foundation:
  - Markdown is the foundation of ShardBase because the user's core knowledge should remain stored in a simple, human-readable text format that can be opened, understood, and edited without requiring ShardBase, Obsidian, an AI agent, or another specialized application.
  - Plain-text Markdown supports long-term data ownership by keeping knowledge in ordinary files that the user can inspect directly, copy, back up, version, search, move, and process with a wide range of existing and future tools.
  - Markdown separates the durability of the user's knowledge from the lifetime of any particular application, plugin, service, synchronization provider, AI provider, or implementation technology.
  - Markdown provides enough document structure for headings, lists, links, tables, code, and other readable content while remaining understandable when enhanced views, queries, scripts, or automation are unavailable.
  - YAML frontmatter complements Markdown by adding explicit machine-readable metadata for structure and semantics without moving that information into a hidden or proprietary database. Humans and software can inspect the same underlying source.
  - Keeping content and metadata together in text files makes ShardBase knowledge suitable for both human reading and machine interpretation, allowing queries, scripts, validation, and AI assistance to operate over information whose underlying representation remains visible to the user.
  - A file-based Markdown foundation supports ShardBase's portability and locality goals because databases can remain understandable and movable as self-contained collections of durable files rather than depending on hidden application state.
  - Markdown is intentionally the foundation rather than the complete ShardBase experience. Obsidian, Dataview, wikilinks, scripts, AI agents, and future tooling may provide richer interaction, but they should enhance the underlying knowledge rather than become the only way that knowledge can be understood.

why_is_obsidian_a_target_environment:
  - Obsidian is ShardBase's primary target environment because it provides a practical, user-facing workspace for interacting with local Markdown files while allowing those files to remain directly accessible outside the application.
  - Obsidian's file-based vault model aligns with ShardBase's goals of user ownership, locality, portability, and inspectability because the knowledge remains stored as ordinary files rather than being hidden behind an application-controlled database.
  - Obsidian provides a strong environment for interconnected knowledge through wikilinks, backlinks, search, navigation, properties, graph-oriented exploration, embeds, and other tools that complement ShardBase's relationship-driven architecture.
  - Obsidian's support for extensibility allows ShardBase to build richer experiences through tools such as Dataview, scripts, templates, views, and future integrations without requiring those enhancements to become the source of truth for the underlying knowledge.
  - Obsidian gives users both direct manual access to their Markdown and opportunities for increasingly sophisticated querying, visualization, navigation, and automation, making it suitable for users who want their knowledge system to grow in capability over time.
  - Obsidian is well suited to ShardBase's modular database model because multiple subjects, databases, views, and supporting resources can coexist inside one vault while the underlying ShardBase architecture preserves their ownership and structural boundaries.
  - Targeting Obsidian gives ShardBase a concrete environment in which to design and validate a coherent user experience instead of attempting to support every Markdown application equally from the beginning.
  - Obsidian is a target environment rather than an architectural dependency. ShardBase's core knowledge, metadata, relationships, and structural meaning should remain understandable and editable even when Obsidian itself is unavailable.

why_is_ai_assistance_part_of_the_design:
  - AI assistance is part of ShardBase because a growing personal knowledge base creates recurring work that benefits from understanding context, relationships, intent, and meaning rather than relying only on rigid rules or exact commands.
  - AI agents can help users classify information, identify likely relationships, retrieve relevant knowledge, explain structure, propose organization, detect inconsistencies, and assist with maintenance across a knowledge base that may span many subjects and databases.
  - ShardBase's explicit structure and metadata give AI agents reliable architectural context, reducing the need to guess fundamental relationships such as database ownership, lineage, immediate parentage, or structural role from filenames or prose alone.
  - AI assistance can reduce the cognitive and repetitive burden of maintaining structured knowledge while allowing the user to focus more on understanding, connecting, creating, and using the knowledge itself.
  - AI is especially valuable where deterministic tooling alone is insufficient, such as interpreting ambiguous information, recognizing semantic relationships, explaining alternatives, or helping the user reason about how new knowledge fits into an existing system.
  - ShardBase should combine AI reasoning with deterministic structure and validation rather than treating either one as sufficient by itself. AI can interpret and recommend; explicit architectural rules can constrain, validate, and make consequential behavior predictable.
  - AI agents should be able to operate as assistants, advisors, architects, auditors, query designers, and other useful roles while remaining subject to ShardBase's architectural rules, privacy expectations, and human-control boundaries.
  - AI assistance must remain optional to the durability and meaning of the knowledge base. ShardBase's core data should remain understandable, editable, and structurally meaningful when AI is unavailable or when the user chooses not to use it.
  - ShardBase should not depend on any particular AI model, provider, or service. Its architecture should allow AI capabilities to evolve without transferring ownership or architectural authority away from the user and their data.

why_is_shardbase_a_framework_instead_of_a_single_database:
  - ShardBase is a framework because a personal source of truth may need to represent many different subjects and areas of life, each with its own scope, semantic metadata, conventions, relationships, and lifecycle needs.
  - A single universal database schema would either become too rigid for diverse kinds of knowledge or grow increasingly complex as it attempted to model every possible domain.
  - ShardBase instead defines a small set of universal structural rules that preserve ownership, lineage, integrity, portability, and interoperability while allowing individual databases to define the domain-specific meaning they need.
  - Each database can remain a coherent, self-contained knowledge boundary with its own purpose, scope, semantic schema, conventions, views, and attachments while still participating in the same broader ShardBase system.
  - The framework model allows users to add, evolve, archive, move, or intentionally version databases independently without requiring unrelated areas of the knowledge base to share the same schema or organizational assumptions.
  - Shared architectural conventions allow humans, Shard, other AI agents, queries, validators, and future tooling to understand how any ShardBase database is structured without requiring every database to contain the same kinds of information.
  - A framework also allows ShardBase itself to evolve independently from the user's domain knowledge: universal architectural improvements can be defined at the framework level while database-specific meaning remains owned by each database.
  - This separation supports long-term extensibility by allowing new knowledge domains, tools, views, automation, and AI capabilities to be added without turning the entire personal knowledge base into one monolithic system.

### Differentiation

why_not_just_use_folders: 
why_not_just_use_tags: 
why_not_just_use_arbitrary_yaml: 
why_not_just_use_dataview_queries: 
why_not_just_use_links_and_backlinks: 
why_not_just_use_an_obsidian_template_system: 
why_not_just_use_a_traditional_database: 
what_does_shardbase_add_that_these_tools_do_not: 
which_existing_tools_should_shardbase_complement_instead_of_replace: 
what_is_the_smallest_unique_idea_at_the_center_of_shardbase: 

### Audience

primary_user: 
primary_user_problem: 
primary_user_skill_level: 
primary_user_workflow: 
secondary_users: 
future_users: 
who_is_shardbase_not_for: 
what_user_behaviors_fit_shardbase_well: 
what_user_behaviors_conflict_with_shardbase: 
does_shardbase_assume_the_user_understands_markdown: 
does_shardbase_assume_the_user_uses_obsidian: 
does_shardbase_assume_the_user_uses_ai: 
how_much_architectural_knowledge_should_a_normal_user_need: 
how_much_architectural_knowledge_should_a_power_user_need: 

### Shard — AI Agent

what_is_shard: 
why_does_shard_exist: 
what_should_shard_be_exceptionally_good_at: 
what_may_shard_do: 
what_must_shard_never_do_without_authorization: 
what_should_shard_infer_automatically: 
what_should_shard_ask_the_user_about: 
what_should_shard_refuse_or_flag_as_invalid: 
how_should_shard_balance_user_intent_and_architectural_validity: 
how_should_shard_preserve_user_control: 
how_should_shard_explain_architectural_decisions: 
what_should_make_shard_trustworthy: 
what_should_make_shard_predictable: 
what_should_make_shard_safe: 

### Design Philosophy

core_design_philosophy: 
minimum_necessary_structure_means: 
human_readability_means: 
ai_readability_means: 
portability_means: 
locality_means: 
inspectability_means: 
queryability_means: 
user_control_means: 
data_ownership_means: 
structural_integrity_means: 
future_growth_means: 
simplicity_means: 
explicitness_means: 
determinism_means: 
what_should_shardbase_optimize_for_first: 
what_should_shardbase_never_optimize_at_the_expense_of_user_data: 

### Guarantees and Expectations

what_should_shardbase_guarantee: 
what_should_shardbase_try_to_guarantee_but_not_promise: 
what_does_shardbase_explicitly_not_guarantee: 
what_should_remain_readable_without_shardbase_tooling: 
what_should_remain_editable_without_shardbase_tooling: 
what_should_remain_portable_without_shardbase_tooling: 
what_should_survive_a_broken_view_or_query: 
what_should_survive_ai_being_unavailable: 
what_should_survive_automation_being_unavailable: 
what_should_never_depend_on_hidden_state: 

### Universal vs Database-Specific Rules

universal_shardbase_rules_are: 
database_specific_rules_are: 
what_belongs_in_the_system_specification: 
what_belongs_in_database_md: 
what_belongs_in_existing_database_conventions: 
what_should_never_be_database_specific: 
what_should_never_be_universal: 
how_should_extensions_be_documented: 
how_should_conflicts_between_local_rules_and_universal_rules_be_handled: 

### Repository vs Local User Data

what_belongs_in_app_blueprints: 
what_belongs_in_app_db: 
what_belongs_in_app_docs: 
what_belongs_in_app_inbox: 
what_belongs_in_app_registry: 
what_belongs_in_app_scripts: 
what_should_be_committed_by_default: 
what_should_be_ignored_by_default: 
what_local_data_may_be_versioned_intentionally: 
what_requires_an_explicit_repository_policy_change: 
what_should_never_be_accidentally_published: 

### Canonical Database Experience

what_should_a_new_database_look_like: 
what_should_database_md_explain: 
how_should_a_database_define_scope: 
how_should_a_database_define_semantic_schema: 
how_should_a_database_define_local_conventions: 
how_should_pools_be_used: 
how_should_cores_be_chosen: 
how_should_shards_be_chosen: 
how_should_pebbles_be_chosen: 
when_should_information_remain_a_heading: 
when_should_a_ghost_shard_be_used: 
what_should_a_good_database_feel_like_to_browse: 
what_should_a_good_database_feel_like_to_query: 
what_should_a_good_database_feel_like_to_edit_manually: 
what_should_a_good_database_feel_like_to_operate_with_shard: 

### Knowledge Lifecycle

how_does_information_enter_shardbase: 
what_is_pre_structural_capture: 
how_is_information_reviewed: 
how_is_database_ownership_determined: 
how_is_pool_membership_determined: 
how_is_core_ownership_determined: 
how_is_immediate_parent_determined: 
how_is_file_materialization_decided: 
how_can_information_grow_over_time: 
how_can_structure_be_refactored_safely: 
how_is_information_archived: 
how_is_information_deleted: 
how_are_orphans_handled: 
how_are_attachments_handled_across_the_lifecycle: 
how_are_ghost_shards_promoted_to_real_notes: 

### Foundation Boundaries

what_is_in_scope_for_foundation: 
what_is_out_of_scope_for_foundation: 
what_must_exist_before_implementation_expands: 
what_can_safely_wait_until_later: 
what_would_be_premature_to_standardize: 
what_should_remain_implementation_defined: 

### Breaking Change Definition

what_counts_as_an_architectural_clarification: 
what_counts_as_an_architectural_extension: 
what_counts_as_a_schema_change: 
what_counts_as_a_migration: 
what_counts_as_a_breaking_change: 
what_changes_require_a_specification_version_change: 
what_changes_require_a_manifest_version_change: 
what_changes_require_database_migration: 
what_changes_must_never_be_silent: 
what_backward_compatibility_should_mean_for_shardbase: 

### Foundation Exit Criteria

when_is_the_product_definition_complete: 
when_is_the_conceptual_language_complete: 
when_is_the_architecture_demonstrable: 
when_is_project_governance_complete: 
when_are_canonical_implementation_artifacts_sufficient: 
when_has_the_foundation_been_proven: 
what_questions_must_have_explicit_answers_before_foundation_complete: 
what_unresolved_questions_are_safe_to_defer: 
who_or_what_decides_foundation_is_complete: 
foundation_completion_statement: 

---

## 3. Milestone 1 — Define the Product

milestone_1_status: approved
milestone_1_goal: Define why ShardBase exists, who it serves, what it is trying to accomplish, and what it deliberately will not become.

### Commit 1 — Product Thesis

commit_01_subject: docs: define shardbase product thesis
commit_01_status: planned
product_thesis_problem: 
product_thesis_observation: 
product_thesis_belief: 
product_thesis_solution: 
product_thesis_unique_value: 
product_thesis_long_term_vision: 
product_thesis_success_looks_like: 

### Commit 2 — Target Users and Use Cases

commit_02_subject: docs: define target users and use cases
commit_02_status: planned
primary_user_profile: 
secondary_user_profiles: 
core_use_case_1: 
core_use_case_2: 
core_use_case_3: 
secondary_use_cases: 
anti_use_cases: 
user_jobs_to_be_done: 
user_pain_points: 
user_success_outcomes: 

### Commit 3 — Goals and Non-Goals

commit_03_subject: docs: define project goals and non-goals
commit_03_status: planned
goal_1: 
goal_2: 
goal_3: 
goal_4: 
goal_5: 
non_goal_1: 
non_goal_2: 
non_goal_3: 
non_goal_4: 
non_goal_5: 
scope_creep_warning_signs: 

### Commit 4 — Design Principles

commit_04_subject: docs: define shardbase design principles
commit_04_status: planned
principle_1_name: 
principle_1_meaning: 
principle_1_tradeoff: 
principle_2_name: 
principle_2_meaning: 
principle_2_tradeoff: 
principle_3_name: 
principle_3_meaning: 
principle_3_tradeoff: 
principle_4_name: 
principle_4_meaning: 
principle_4_tradeoff: 
principle_5_name: 
principle_5_meaning: 
principle_5_tradeoff: 
principle_priority_when_conflicts_occur: 

### Commit 5 — Foundation Success Criteria

commit_05_subject: docs: define foundation success criteria
commit_05_status: planned
foundation_success_product: 
foundation_success_architecture: 
foundation_success_safety: 
foundation_success_understandability: 
foundation_success_implementability: 
foundation_success_stability: 
foundation_failure_conditions: 

---

## 4. Milestone 2 — Define the Conceptual Language

milestone_2_status: approved
milestone_2_goal: Give ShardBase a canonical vocabulary and decision model so humans, documentation, Shard, and future tooling use the same concepts consistently.

### Commit 6 — Terminology Glossary

commit_06_subject: docs: add shardbase terminology glossary
commit_06_status: planned
term_pool: 
term_core: 
term_shard: 
term_pebble: 
term_ghost_shard: 
term_database: 
term_database_manifest: 
term_structural_metadata: 
term_semantic_metadata: 
term_lineage: 
term_root_core: 
term_immediate_parent: 
term_materialization: 
term_migration: 
term_blueprint: 
term_registry: 
term_inbox: 
term_view: 
term_attachment: 
additional_terms_needed: 

### Commit 7 — Structural vs Semantic Concepts

commit_07_subject: docs: define structural versus semantic concepts
commit_07_status: planned
structural_metadata_purpose: 
semantic_metadata_purpose: 
reserved_structural_fields: 
examples_of_semantic_fields: 
structural_semantic_boundary_rule: 
common_category_mistakes: 
how_to_resolve_ambiguous_fields: 

### Commit 8 — Knowledge Lifecycle Model

commit_08_subject: docs: define knowledge lifecycle model
commit_08_status: planned
lifecycle_stage_capture: 
lifecycle_stage_review: 
lifecycle_stage_classification: 
lifecycle_stage_materialization: 
lifecycle_stage_growth: 
lifecycle_stage_refactor: 
lifecycle_stage_archive: 
lifecycle_stage_delete: 
lifecycle_transition_rules: 
lifecycle_safety_rules: 

### Commit 9 — Database Ownership Model

commit_09_subject: docs: define database ownership model
commit_09_status: planned
database_owns: 
database_does_not_own: 
cross_database_relationship_policy: 
cross_database_attachment_policy: 
cross_database_view_policy: 
cross_database_schema_policy: 
ownership_ambiguity_resolution: 
database_portability_expectation: 

### Commit 10 — Structural Decision Framework

commit_10_subject: docs: define structural decision framework
commit_10_status: planned
choose_core_when: 
choose_shard_when: 
choose_pebble_when: 
choose_heading_when: 
choose_ghost_shard_when: 
independent_lifecycle_test: 
independent_querying_test: 
independent_navigation_test: 
independent_reuse_test: 
future_growth_test: 
minimum_structure_test: 
decision_tie_breaker: 

---

## 5. Milestone 3 — Make the Architecture Demonstrable

milestone_3_status: approved
milestone_3_goal: Make the architecture understandable through canonical examples, walkthroughs, and failure cases rather than relying on normative rules alone.

### Commit 11 — Canonical Database Walkthrough

commit_11_subject: docs: add canonical database walkthrough
commit_11_status: planned
walkthrough_domain: 
walkthrough_database_name: 
walkthrough_database_id: 
walkthrough_data_folder: 
walkthrough_pool_strategy: 
walkthrough_core_strategy: 
walkthrough_story_start: 
walkthrough_story_growth: 
walkthrough_story_end_state: 
why_this_example_is_canonical: 

### Commit 12 — Structural Classification Examples

commit_12_subject: docs: add structural classification examples
commit_12_status: planned
good_core_example: 
bad_core_example: 
good_shard_example: 
bad_shard_example: 
good_pebble_example: 
bad_pebble_example: 
good_heading_example: 
bad_heading_example: 
good_ghost_shard_example: 
bad_ghost_shard_example: 
ambiguous_case_examples: 

### Commit 13 — Lineage and Naming Examples

commit_13_subject: docs: add lineage and naming examples
commit_13_status: planned
canonical_lineage_example: 
recursive_naming_example: 
metadata_lineage_example: 
filename_metadata_mismatch_example: 
full_ancestry_filename_anti_example: 
renaming_safety_example: 

### Commit 14 — Database Manifest Example

commit_14_subject: docs: add database manifest example
commit_14_status: planned
canonical_manifest_domain: 
canonical_manifest_frontmatter: 
canonical_manifest_purpose: 
canonical_manifest_scope_includes: 
canonical_manifest_scope_excludes: 
canonical_manifest_architecture: 
canonical_manifest_schema: 
canonical_manifest_conventions: 
canonical_manifest_resources: 

### Commit 15 — Common Architecture Mistakes

commit_15_subject: docs: document common architecture mistakes
commit_15_status: planned
mistake_premature_fragmentation: 
mistake_semantic_type_overload: 
mistake_nested_database_roots: 
mistake_accumulated_filename_ancestry: 
mistake_invalid_parent_lineage: 
mistake_pebble_parent: 
mistake_cross_database_attachment_ownership: 
mistake_view_as_authority: 
mistake_blueprint_synchronization: 
mistake_destructive_normalization: 
additional_common_mistakes: 

---

## 6. Milestone 4 — Establish Project Governance

milestone_4_status: approved
milestone_4_goal: Define how ShardBase itself evolves without making architectural changes ambiguous, silent, destructive, or implementation-driven.

### Commit 16 — Architectural Change Policy

commit_16_subject: docs: define architectural change policy
commit_16_status: planned
change_category_clarification: 
change_category_extension: 
change_category_schema_change: 
change_category_migration: 
change_category_breaking_change: 
required_review_for_each_category: 
required_documentation_for_each_category: 
change_approval_model: 

### Commit 17 — Specification Versioning Policy

commit_17_subject: docs: define specification versioning policy
commit_17_status: planned
system_spec_version_scheme: 
manifest_version_scheme: 
semantic_schema_versioning_expectation: 
when_to_increment_versions: 
how_versions_are_recorded: 
how_old_versions_are_supported: 
versioning_non_goals: 

### Commit 18 — Migration Principles

commit_18_subject: docs: define migration principles
commit_18_status: planned
migration_primary_goal: 
migration_preservation_rule: 
migration_backup_expectation: 
migration_dry_run_expectation: 
migration_validation_expectation: 
migration_failure_behavior: 
migration_rollback_expectation: 
migration_user_approval_requirement: 
migration_blueprint_rule: 

### Commit 19 — Architecture Decision Records

commit_19_subject: docs: add architecture decision records
commit_19_status: planned
adr_location: 
adr_filename_convention: 
adr_required_fields: 
adr_status_values: 
when_an_adr_is_required: 
when_an_adr_is_not_required: 
how_adrs_relate_to_system_specification: 
how_adrs_are_superseded: 

### Commit 20 — Compatibility Policy

commit_20_subject: docs: define compatibility policy
commit_20_status: planned
architectural_compatibility_means: 
database_compatibility_means: 
manifest_compatibility_means: 
tooling_compatibility_means: 
runtime_compatibility_means: 
obsidian_compatibility_means: 
ai_provider_compatibility_means: 
what_is_deferred_until_implementation_requires_it: 

---

## 7. Milestone 5 — Create the First Canonical Implementation Artifacts

milestone_5_status: approved
milestone_5_goal: Turn the foundation specification into the smallest useful set of canonical artifacts and deterministic validation behavior.

### Commit 21 — Minimal Database Blueprint

commit_21_subject: blueprint: add minimal database blueprint
commit_21_status: planned
blueprint_minimum_contents: 
blueprint_manifest_defaults: 
blueprint_placeholder_policy: 
blueprint_views_policy: 
blueprint_structural_content_policy: 
blueprint_materialization_boundary: 
blueprint_upgrade_policy: explicit migration only

### Commit 22 — Registry Discovery Contract

commit_22_subject: registry: define database discovery contract
commit_22_status: planned
registry_discovery_source: 
registry_valid_database_test: 
registry_display_fields: 
registry_invalid_database_behavior: 
registry_authority_boundary: 
registry_manual_vs_generated_behavior: 

### Commit 23 — Database Manifest Validation

commit_23_subject: validate: add database manifest validation
commit_23_status: planned
validate_database_location: 
validate_database_md_exists: 
validate_manifest_fields: 
validate_manifest_values: 
validate_data_folder: 
validate_required_body_sections: 
validation_output_format: 
validation_failure_behavior: 

### Commit 24 — Structural Metadata Validation

commit_24_subject: validate: add structural metadata validation
commit_24_status: planned
validate_required_structural_fields: 
validate_type: 
validate_pool: 
validate_core: 
validate_parent_note: 
validate_status: 
validate_structural_semantic_separation: 

### Commit 25 — Lineage Integrity Checks

commit_25_subject: validate: add lineage integrity checks
commit_25_status: planned
validate_core_self_reference: 
validate_parent_exists: 
validate_no_self_parent: 
validate_no_cycles: 
validate_no_self_ancestor: 
validate_root_core: 
validate_pebble_terminal: 
validate_missing_parent_behavior: 

### Commit 26 — Naming and Placement Checks

commit_26_subject: validate: add naming and placement checks
commit_26_status: planned
validate_core_filename: 
validate_supporting_filename: 
validate_immediate_parent_naming: 
validate_no_full_ancestry_accumulation: 
validate_primary_heading: 
validate_file_location: 
validate_filename_metadata_consistency: 

### Commit 27 — Markdown Structure Checks

commit_27_subject: validate: add markdown structure checks
commit_27_status: planned
validate_heading_sequence: 
validate_heading_blank_line: 
validate_structural_heading_usage: 
validate_empty_headings: 
markdown_validation_scope: 

### Commit 28 — Canonical Validation Fixtures

commit_28_subject: test: add canonical validation fixtures
commit_28_status: planned
fixture_valid_database: 
fixture_invalid_manifest: 
fixture_invalid_type: 
fixture_invalid_core: 
fixture_missing_parent: 
fixture_cycle: 
fixture_pebble_parent: 
fixture_bad_filename: 
fixture_bad_heading_structure: 
fixture_fragmentation_case: 
fixture_attachment_violation: 
fixture_inbox_case: 
fixture_expected_result_format: 

---

## 8. Milestone 6 — Prove the Entire Foundation

milestone_6_status: approved
milestone_6_goal: Demonstrate that the foundation is coherent, teachable, testable, and stable enough to build future implementation work against.

### Commit 29 — Canonical Example Database

commit_29_subject: example: add canonical shardbase database
commit_29_status: planned
example_database_domain: 
example_database_purpose: 
example_database_scope: 
example_database_complexity: 
example_database_lineages: 
example_database_views: 
example_database_attachments: 
example_database_reason_for_inclusion: 

### Commit 30 — End-to-End Shard Workflow

commit_30_subject: docs: document end-to-end shard workflow
commit_30_status: planned
workflow_capture: 
workflow_review: 
workflow_database_selection: 
workflow_pool_selection: 
workflow_core_selection: 
workflow_parent_selection: 
workflow_classification: 
workflow_materialization: 
workflow_validation: 
workflow_query_and_navigation: 
workflow_growth: 
workflow_archive: 

### Commit 31 — Foundation Architecture Overview

commit_31_subject: docs: add foundation architecture overview
commit_31_status: planned
architecture_overview_purpose: 
architecture_overview_audience: 
architecture_overview_repository_map: 
architecture_overview_authority_map: 
architecture_overview_database_map: 
architecture_overview_lineage_map: 
architecture_overview_lifecycle_map: 
architecture_overview_safety_map: 

### Commit 32 — Foundation Decision Log

commit_32_subject: docs: add foundation decision log
commit_32_status: planned
decision_log_purpose: 
decisions_to_capture: 
alternatives_to_capture: 
rejected_approaches_to_capture: 
relationship_to_adrs: 
relationship_to_system_specification: 

### Commit 33 — Post-Foundation Roadmap

commit_33_subject: docs: define post-foundation roadmap
commit_33_status: planned
next_stage_name: 
next_stage_primary_goal: 
next_stage_entry_requirements: 
first_post_foundation_priorities: 
features_to_reconsider: 
implementation_questions_to_revisit: 
long_term_roadmap_categories: 

### Commit 34 — Foundation Completion

commit_34_subject: release: complete shardbase foundation
commit_34_status: planned
foundation_completion_version_or_marker: 
foundation_completion_date: 
foundation_completion_summary: 
foundation_known_limitations: 
foundation_deferred_work: 
foundation_compatibility_statement: 
foundation_next_stage: 

---

## 9. Deliberately Deferred Features

deferred_status: approved
deferred_reason: Avoid allowing implementation choices to dictate architecture before the foundation is stable.

full_cli: deferred
interactive_database_creation_wizard: deferred
automated_inbox_classification: deferred
llm_provider_integration: deferred
database_migration_engine: deferred
schema_migration_framework: deferred
obsidian_plugin: deferred
sync_system: deferred
search_and_indexing_engine: deferred
api_server: deferred
web_ui: deferred
packaging_and_distribution_system: deferred
extensive_dataview_dashboards: deferred
plugin_version_compatibility_matrix: deferred
cloud_infrastructure: deferred

feature_most_exciting_for_later: 
feature_most_likely_to_be_needed_first: 
feature_most_architecturally_risky: 
feature_that_should_remain_optional: 
additional_deferred_features: 

---

## 10. Foundation Definition of Done

definition_of_done_status: approved

### Product

dod_purpose_is_explicit: complete
dod_target_users_are_explicit: incomplete
dod_primary_use_cases_are_explicit: incomplete
dod_goals_are_explicit: incomplete
dod_non_goals_are_explicit: incomplete

### Architecture

dod_universal_invariants_are_documented: largely-established
dod_vocabulary_is_canonical: incomplete
dod_database_ownership_is_unambiguous: partially-established
dod_structural_classification_is_unambiguous: partially-established
dod_lifecycle_behavior_is_defined: incomplete
dod_lineage_behavior_is_defined: largely-established

### Safety

dod_user_owned_data_protections_are_documented: largely-established
dod_migration_principles_are_defined: incomplete
dod_breaking_change_expectations_are_defined: incomplete

### Understandability

dod_newcomer_can_understand_without_source_code: incomplete
dod_complete_example_database_exists: incomplete
dod_good_and_bad_examples_exist: incomplete

### Implementability

dod_minimal_blueprint_exists: incomplete
dod_structural_rules_can_be_validated_deterministically: specification-exists-implementation-incomplete
dod_validation_fixtures_prove_expected_behavior: incomplete

### Stability

dod_major_architectural_questions_for_initial_implementation_are_answered: incomplete
dod_remaining_questions_are_safe_to_defer: incomplete
dod_foundation_can_be_declared_stable: incomplete

definition_of_done_final_review_notes: 
definition_of_done_blockers: 
definition_of_done_accepted_deferred_items: 

---

## 11. Open Questions and Parking Lot

open_question_01: 
open_question_02: 
open_question_03: 
open_question_04: 
open_question_05: 
open_question_06: 
open_question_07: 
open_question_08: 
open_question_09: 
open_question_10: 

idea_parking_lot_01:
  - Vault/runtime boundary: Generated runtimes, installed dependencies, caches, and other machine-specific execution artifacts should remain outside the ShardBase vault by default. ShardBase should minimize unnecessary filesystem noise and synchronization burden while keeping durable framework resources inside the vault inspectable and portable.
  - Revisit and incorporate this principle when defining `locality_means`, `portability_means`, `what_belongs_in_app_scripts`, `what_should_be_committed_by_default`, `what_should_be_ignored_by_default`, and implementation-specific compatibility or tooling policies.

idea_parking_lot_02: 
idea_parking_lot_03: 
idea_parking_lot_04: 
idea_parking_lot_05: 

future_feature_idea_01: 
future_feature_idea_02: 
future_feature_idea_03: 
future_feature_idea_04: 
future_feature_idea_05: 

decision_needing_research_01: 
decision_needing_research_02: 
decision_needing_research_03: 

---

## 12. Review Log

review_round_01_date: 
review_round_01_focus: 
review_round_01_decisions: 
review_round_01_open_items: 

review_round_02_date: 
review_round_02_focus: 
review_round_02_decisions: 
review_round_02_open_items: 

review_round_03_date: 
review_round_03_focus: 
review_round_03_decisions: 
review_round_03_open_items: 

---

## 13. Anchor Commit

anchor_commit_purpose: Preserve the approved foundation roadmap and create a durable brainstorming workbook before longer product-definition work begins.
anchor_commit_subject: docs: add foundation roadmap workbook
anchor_commit_status: complete
anchor_commit_scope: Add the foundation-stage workbook containing the approved six-milestone roadmap, foundational questions, deferred features, and Definition of Done.
anchor_commit_architectural_effect: None. This is a planning document and does not override the System Specification.
anchor_commit_deferred_behavior: Product answers, conceptual definitions, governance policies, implementation artifacts, and foundation proof remain future focused commits.

### Suggested Commit Message

```text
docs: add foundation roadmap workbook

Capture the approved six-milestone ShardBase foundation plan and create a
working key-value template for product, conceptual, architectural,
governance, implementation, and validation decisions.

Record the foundation Definition of Done and explicitly deferred features
so future work can proceed from a stable planning checkpoint.

Keep the workbook non-authoritative; the Shard System Specification
remains the highest architectural authority.
```

---

## 14. Final Foundation Sign-Off

foundation_product_definition_approved: no
foundation_conceptual_language_approved: no
foundation_demonstrable_architecture_approved: no
foundation_governance_approved: no
foundation_canonical_implementation_approved: no
foundation_proof_approved: no
foundation_definition_of_done_satisfied: no
foundation_ready_to_close: no

final_foundation_notes: 
