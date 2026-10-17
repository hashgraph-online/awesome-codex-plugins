/* ###
 * IP: personal-local-plugins
 */
// Export Ghidra decompiler pseudocode to disk for artifact-driven Rust RE workflows.
//@category ReverseEngineering

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Instant;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.decompiler.DecompiledFunction;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import ghidra.program.model.symbol.Namespace;

public class ExportRustPseudocode extends GhidraScript {

	private static final int DEFAULT_MAX_FUNCTIONS = 0;
	private static final int DEFAULT_TIMEOUT_SECONDS = 60;
	private static final int MAX_FILE_NAME_CHARS = 120;

	@Override
	protected void run() throws Exception {
		String[] args = getScriptArgs();
		if (args.length < 1) {
			throw new IllegalArgumentException(
				"Expected output directory, optional max-function count, and optional timeout seconds");
		}

		File outputDir = new File(args[0]);
		int maxFunctions = parsePositiveInt(args, 1, DEFAULT_MAX_FUNCTIONS);
		int timeoutSeconds = parsePositiveInt(args, 2, DEFAULT_TIMEOUT_SECONDS);

		File functionsDir = new File(outputDir, "functions");
		if (!functionsDir.exists() && !functionsDir.mkdirs()) {
			throw new IOException("Failed to create output directory: " + functionsDir.getAbsolutePath());
		}

		Path indexPath = new File(outputDir, "functions.tsv").toPath();
		Path errorPath = new File(outputDir, "decompile-errors.tsv").toPath();
		Path statusPath = new File(outputDir, "status.txt").toPath();
		Path summaryPath = new File(outputDir, "summary.txt").toPath();
		Path completeMarkerPath = new File(outputDir, "complete.marker").toPath();
		Path failedMarkerPath = new File(outputDir, "failed.marker").toPath();
		Path interruptedMarkerPath = new File(outputDir, "interrupted.marker").toPath();

		writeString(indexPath,
			"index\tentry\tname\tnamespace\tbody_addresses\tstatus\tpseudocode_path\tsignature\n");
		writeString(errorPath, "index\tentry\tname\terror\n");
		deleteIfExists(completeMarkerPath);
		deleteIfExists(failedMarkerPath);
		deleteIfExists(interruptedMarkerPath);

		int processed = 0;
		int emitted = 0;
		int failed = 0;
		int timedOut = 0;
		int cancelled = 0;
		long totalChars = 0L;
		String state = "running";
		String startedAt = nowIso();
		String lastUpdateAt = startedAt;
		String completedAt = "";
		String lastFunctionEntry = "";
		String lastFunctionName = "";
		String lastError = "";

		writeProgress(statusPath, summaryPath, state, startedAt, lastUpdateAt, completedAt,
			processed, emitted, failed, timedOut, cancelled,
			timeoutSeconds, maxFunctions, totalChars,
			lastFunctionEntry, lastFunctionName, lastError);

		DecompInterface decompiler = new DecompInterface();
		DecompileOptions options = new DecompileOptions();
		decompiler.setOptions(options);
		decompiler.toggleCCode(true);
		decompiler.toggleSyntaxTree(false);
		decompiler.setSimplificationStyle("decompile");

		try {
			if (!decompiler.openProgram(currentProgram)) {
				state = "failed";
				lastError = sanitizeField(decompiler.getLastMessage());
				throw new IOException("Failed to open program in decompiler: " + decompiler.getLastMessage());
			}

			FunctionIterator iterator = currentProgram.getFunctionManager().getFunctionsNoStubs(true);
			while (iterator.hasNext() && !monitor.isCancelled()) {
				Function function = iterator.next();
				if (function == null || function.isExternal()) {
					continue;
				}
				if (maxFunctions > 0 && processed >= maxFunctions) {
					break;
				}

				processed++;
				monitor.setMessage("Decompiling " + function.getName());
				lastFunctionEntry = function.getEntryPoint().toString();
				lastFunctionName = function.getName();
				lastError = "";

				String entry = function.getEntryPoint().toString();
				String name = function.getName();
				String namespace = getNamespaceName(function);
				long bodyAddresses = function.getBody().getNumAddresses();
				String signature = sanitizeField(function.getPrototypeString(true, true));
				String pseudocodePath = "";
				String status = "error";
				String error = "";

				DecompileResults results =
					decompiler.decompileFunction(function, timeoutSeconds, monitor);

				if (results == null) {
					failed++;
					error = "null decompile result";
				}
				else if (results.isCancelled()) {
					cancelled++;
					status = "cancelled";
					error = sanitizeField(results.getErrorMessage());
				}
				else if (results.isTimedOut()) {
					timedOut++;
					status = "timeout";
					error = sanitizeField(results.getErrorMessage());
				}
				else if (!results.decompileCompleted() || !results.isValid()) {
					failed++;
					error = sanitizeField(results.getErrorMessage());
				}
				else {
					DecompiledFunction decompiledFunction = results.getDecompiledFunction();
					if (decompiledFunction == null) {
						failed++;
						error = "missing decompiled function";
					}
					else {
						String cText = decompiledFunction.getC();
						if (cText == null || cText.isEmpty()) {
							failed++;
							error = "empty pseudocode output";
						}
						else {
							status = "ok";
							signature = sanitizeField(decompiledFunction.getSignature());
							String fileName = buildFileName(processed, entry, name);
							pseudocodePath = "functions/" + fileName;
							writeString(
								new File(outputDir, pseudocodePath).toPath(),
								buildPseudocodeHeader(function, namespace, signature) + cText + "\n");
							emitted++;
							totalChars += cText.length();
						}
					}
				}

				appendString(indexPath,
					processed + "\t" +
						sanitizeField(entry) + "\t" +
						sanitizeField(name) + "\t" +
						sanitizeField(namespace) + "\t" +
						bodyAddresses + "\t" +
						status + "\t" +
						sanitizeField(pseudocodePath) + "\t" +
						signature + "\n");

				if (!error.isEmpty()) {
					lastError = error;
					appendString(errorPath,
						processed + "\t" +
							sanitizeField(entry) + "\t" +
							sanitizeField(name) + "\t" +
							error + "\n");
				}

				lastUpdateAt = nowIso();
				writeProgress(statusPath, summaryPath, state, startedAt, lastUpdateAt, completedAt,
					processed, emitted, failed, timedOut, cancelled,
					timeoutSeconds, maxFunctions, totalChars,
					lastFunctionEntry, lastFunctionName, lastError);
			}

			state = monitor.isCancelled() ? "interrupted" : "completed";
		}
		catch (Exception e) {
			if (!"interrupted".equals(state)) {
				state = "failed";
			}
			if (lastError == null || lastError.isEmpty()) {
				lastError = sanitizeField(e.toString());
			}
			throw e;
		}
		finally {
			decompiler.dispose();
			lastUpdateAt = nowIso();
			if ("completed".equals(state)) {
				completedAt = lastUpdateAt;
				touch(completeMarkerPath);
			}
			else if ("interrupted".equals(state)) {
				touch(interruptedMarkerPath);
			}
			else if ("failed".equals(state)) {
				touch(failedMarkerPath);
			}
			writeProgress(statusPath, summaryPath, state, startedAt, lastUpdateAt, completedAt,
				processed, emitted, failed, timedOut, cancelled,
				timeoutSeconds, maxFunctions, totalChars,
				lastFunctionEntry, lastFunctionName, lastError);
		}
	}

	private int parsePositiveInt(String[] args, int index, int defaultValue) {
		if (index >= args.length || args[index] == null || args[index].isEmpty()) {
			return defaultValue;
		}
		int parsed = Integer.parseInt(args[index]);
		if (parsed < 0) {
			throw new IllegalArgumentException("Expected non-negative integer at argument " + index);
		}
		return parsed;
	}

	private String getNamespaceName(Function function) {
		Namespace namespace = function.getParentNamespace();
		if (namespace == null) {
			return "";
		}
		return namespace.getName(true);
	}

	private String buildFileName(int index, String entry, String name) {
		String stem = String.format("%05d_%s_%s.c",
			index,
			sanitizeFilePart(entry),
			sanitizeFilePart(name));
		if (stem.length() <= MAX_FILE_NAME_CHARS) {
			return stem;
		}
		int suffixLength = ".c".length();
		return stem.substring(0, MAX_FILE_NAME_CHARS - suffixLength) + ".c";
	}

	private String sanitizeFilePart(String value) {
		String sanitized = value.replaceAll("[^A-Za-z0-9._-]+", "_");
		sanitized = sanitized.replaceAll("_+", "_");
		sanitized = sanitized.replaceAll("^_+", "");
		sanitized = sanitized.replaceAll("_+$", "");
		if (sanitized.isEmpty()) {
			return "unnamed";
		}
		return sanitized;
	}

	private String sanitizeField(String value) {
		if (value == null) {
			return "";
		}
		return value.replace('\t', ' ')
			.replace('\r', ' ')
			.replace('\n', ' ')
			.trim();
	}

	private String buildPseudocodeHeader(Function function, String namespace, String signature) {
		StringBuilder builder = new StringBuilder();
		builder.append("/*\n");
		builder.append(" * Ghidra headless pseudocode export\n");
		builder.append(" * Program: ").append(currentProgram.getName()).append("\n");
		builder.append(" * Executable path: ").append(currentProgram.getExecutablePath()).append("\n");
		builder.append(" * Function: ").append(function.getName()).append("\n");
		builder.append(" * Namespace: ").append(namespace).append("\n");
		builder.append(" * Entry: ").append(function.getEntryPoint()).append("\n");
		builder.append(" * Signature: ").append(signature).append("\n");
		builder.append(" * Note: Decompiled pseudocode, not original Rust source.\n");
		builder.append(" */\n\n");
		return builder.toString();
	}

	private void writeProgress(Path statusPath, Path summaryPath, String state,
			String startedAt, String lastUpdateAt, String completedAt,
			int processed, int emitted, int failed, int timedOut, int cancelled,
			int timeoutSeconds, int maxFunctions, long totalChars,
			String lastFunctionEntry, String lastFunctionName, String lastError) throws IOException {
		writeString(statusPath, buildStatus(state, startedAt, lastUpdateAt, completedAt,
			processed, emitted, failed, timedOut, cancelled,
			lastFunctionEntry, lastFunctionName, lastError));
		writeString(summaryPath, buildSummary(state, startedAt, lastUpdateAt, completedAt,
			processed, emitted, failed, timedOut, cancelled,
			timeoutSeconds, maxFunctions, totalChars,
			lastFunctionEntry, lastFunctionName, lastError));
	}

	private String buildStatus(String state, String startedAt, String lastUpdateAt, String completedAt,
			int processed, int emitted, int failed, int timedOut, int cancelled,
			String lastFunctionEntry, String lastFunctionName, String lastError) {
		StringBuilder builder = new StringBuilder();
		builder.append("STATE: ").append(state).append("\n");
		builder.append("STARTED_AT: ").append(startedAt).append("\n");
		builder.append("LAST_UPDATE_AT: ").append(lastUpdateAt).append("\n");
		builder.append("COMPLETED_AT: ").append(completedAt).append("\n");
		builder.append("FUNCTIONS_PROCESSED: ").append(processed).append("\n");
		builder.append("PSEUDOCODE_FILES_WRITTEN: ").append(emitted).append("\n");
		builder.append("DECOMPILATION_FAILURES: ").append(failed).append("\n");
		builder.append("DECOMPILATION_TIMEOUTS: ").append(timedOut).append("\n");
		builder.append("DECOMPILATION_CANCELLED: ").append(cancelled).append("\n");
		builder.append("LAST_FUNCTION_ENTRY: ").append(sanitizeField(lastFunctionEntry)).append("\n");
		builder.append("LAST_FUNCTION_NAME: ").append(sanitizeField(lastFunctionName)).append("\n");
		builder.append("LAST_ERROR: ").append(sanitizeField(lastError)).append("\n");
		return builder.toString();
	}

	private String buildSummary(String state, String startedAt, String lastUpdateAt, String completedAt,
			int processed, int emitted, int failed, int timedOut, int cancelled,
			int timeoutSeconds, int maxFunctions, long totalChars,
			String lastFunctionEntry, String lastFunctionName, String lastError) {
		StringBuilder builder = new StringBuilder();
		builder.append("STATE: ").append(state).append("\n");
		builder.append("STARTED_AT: ").append(startedAt).append("\n");
		builder.append("LAST_UPDATE_AT: ").append(lastUpdateAt).append("\n");
		builder.append("COMPLETED_AT: ").append(completedAt).append("\n");
		builder.append("PROGRAM: ").append(currentProgram.getName()).append("\n");
		builder.append("EXECUTABLE_PATH: ").append(currentProgram.getExecutablePath()).append("\n");
		builder.append("EXECUTABLE_FORMAT: ").append(currentProgram.getExecutableFormat()).append("\n");
		builder.append("LANGUAGE: ").append(currentProgram.getLanguageID()).append("\n");
		builder.append("COMPILER: ").append(currentProgram.getCompiler()).append("\n");
		builder.append("FUNCTIONS_PROCESSED: ").append(processed).append("\n");
		builder.append("PSEUDOCODE_FILES_WRITTEN: ").append(emitted).append("\n");
		builder.append("DECOMPILATION_FAILURES: ").append(failed).append("\n");
		builder.append("DECOMPILATION_TIMEOUTS: ").append(timedOut).append("\n");
		builder.append("DECOMPILATION_CANCELLED: ").append(cancelled).append("\n");
		builder.append("PER_FUNCTION_TIMEOUT_SECONDS: ").append(timeoutSeconds).append("\n");
		builder.append("MAX_FUNCTIONS: ").append(maxFunctions == 0 ? "all" : Integer.toString(maxFunctions))
			.append("\n");
		builder.append("TOTAL_PSEUDOCODE_CHARACTERS: ").append(totalChars).append("\n");
		builder.append("LAST_FUNCTION_ENTRY: ").append(sanitizeField(lastFunctionEntry)).append("\n");
		builder.append("LAST_FUNCTION_NAME: ").append(sanitizeField(lastFunctionName)).append("\n");
		builder.append("LAST_ERROR: ").append(sanitizeField(lastError)).append("\n");
		builder.append("FILES_INDEX: functions.tsv\n");
		builder.append("FILES_ERRORS: decompile-errors.tsv\n");
		builder.append("FILES_DIR: functions/\n");
		builder.append("STATUS_FILE: status.txt\n");
		builder.append("COMPLETE_MARKER: complete.marker\n");
		return builder.toString();
	}

	private String nowIso() {
		return Instant.now().toString();
	}

	private void deleteIfExists(Path path) throws IOException {
		Files.deleteIfExists(path);
	}

	private void touch(Path path) throws IOException {
		Files.writeString(path, "", StandardCharsets.UTF_8,
			StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
	}

	private void writeString(Path path, String content) throws IOException {
		Files.writeString(path, content, StandardCharsets.UTF_8,
			StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
	}

	private void appendString(Path path, String content) throws IOException {
		Files.writeString(path, content, StandardCharsets.UTF_8,
			StandardOpenOption.CREATE, StandardOpenOption.APPEND);
	}
}
