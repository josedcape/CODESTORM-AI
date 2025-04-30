
/**
 * debug-ai.js - Script para el depurador automático de código con IA
 * 
 * Este script proporciona funcionalidad para detectar, diagnosticar y corregir
 * automáticamente errores comunes en diferentes lenguajes de programación.
 */

class DebugAI {
    constructor(options = {}) {
        this.options = {
            autoDetect: true,
            deepDiagnosis: true,
            suggestFixes: true,
            ...options
        };
        
        this.supportedLanguages = [
            'python', 'javascript', 'typescript', 'java', 
            'cpp', 'csharp', 'php', 'ruby', 'go'
        ];
        
        // Common error patterns by language
        this.errorPatterns = {
            python: {
                'SyntaxError: invalid syntax': {
                    patterns: [
                        { regex: /print\s+([^(].*$)/gm, fix: 'print($1)', description: 'La función print requiere paréntesis en Python 3' },
                        { regex: /except\s+(\w+)\s*,\s*(\w+)/g, fix: 'except $1 as $2', description: 'Sintaxis de excepciones incorrecta' },
                        { regex: /([^=!<>])=([^=])/g, fix: '$1==$2', description: 'Operador de asignación usado en lugar de comparación' }
                    ]
                },
                'IndentationError': {
                    patterns: [
                        { regex: /^\s*(\w+)/gm, fix: '    $1', description: 'Indentación inconsistente' }
                    ]
                },
                'NameError: name \'(\\w+)\' is not defined': {
                    patterns: [
                        { regex: /([a-zA-Z_][a-zA-Z0-9_]*)/g, checkDefined: true, description: 'Variable no definida' }
                    ]
                }
            },
            javascript: {
                'SyntaxError: Unexpected token': {
                    patterns: [
                        { regex: /for\s*\(.*\)\s*{([^}]*)}/, fix: 'for () {\n$1\n}', description: 'Falta de llaves o estructura incorrecta en bucle for' },
                        { regex: /if\s*\(.*\)\s*([^{].*)/, fix: 'if () {\n    $1\n}', description: 'Falta de llaves en condicional if' }
                    ]
                },
                'TypeError: (\\w+) is not a function': {
                    patterns: [
                        { regex: /(\w+)\(\)/, checkType: 'function', description: 'Intento de llamar a algo que no es una función' }
                    ]
                }
            }
        };
    }
    
    /**
     * Analiza el código y detecta posibles errores
     * @param {string} code - El código a analizar
     * @param {string} language - El lenguaje del código
     * @param {string} errorMessage - Mensaje de error opcional
     * @returns {Object} Resultado del diagnóstico
     */
    diagnose(code, language, errorMessage = '') {
        if (!this.supportedLanguages.includes(language)) {
            return {
                success: false,
                message: `El lenguaje ${language} no está soportado para diagnóstico automático.`
            };
        }
        
        // Resultados del diagnóstico
        const result = {
            success: true,
            language,
            errorType: 'unknown',
            errorLocation: null,
            fixes: [],
            diagnosis: '',
            fixedCode: code
        };
        
        // Si hay un mensaje de error, intentar identificar el tipo
        if (errorMessage) {
            // Extraer tipo de error y línea si es posible
            const errorTypeMatch = errorMessage.match(/([A-Za-z]+Error):/);
            const lineMatch = errorMessage.match(/line\s+(\d+)/);
            
            if (errorTypeMatch) {
                result.errorType = errorTypeMatch[1];
            }
            
            if (lineMatch) {
                result.errorLocation = parseInt(lineMatch[1]);
            }
            
            // Buscar patrones de error conocidos para el lenguaje
            if (this.errorPatterns[language]) {
                // Buscar en cada patrón de error para este lenguaje
                for (const [errorPattern, patterns] of Object.entries(this.errorPatterns[language])) {
                    const regex = new RegExp(errorPattern);
                    if (regex.test(errorMessage)) {
                        // Aplicar los patrones de corrección
                        let fixedCode = code;
                        patterns.patterns.forEach(pattern => {
                            fixedCode = fixedCode.replace(pattern.regex, pattern.fix || '');
                            result.fixes.push({
                                description: pattern.description,
                                applied: fixedCode !== code
                            });
                        });
                        result.fixedCode = fixedCode;
                        break;
                    }
                }
            }
        } else {
            // Sin mensaje de error, intentar detectar problemas comunes
            // Esto podría ser una inspección general de buenas prácticas
            result.diagnosis = 'No se proporcionó un mensaje de error específico. Realizado diagnóstico general.';
            
            // Ejemplo de diagnóstico general para Python
            if (language === 'python') {
                // Verificar imports no utilizados
                const imports = code.match(/^import\s+(\w+)/gm) || [];
                const unusedImports = imports.filter(imp => {
                    const module = imp.replace('import ', '').trim();
                    return !new RegExp(`(?<!["'])${module}\\.`).test(code);
                });
                
                if (unusedImports.length > 0) {
                    result.fixes.push({
                        description: `Encontrados ${unusedImports.length} imports no utilizados`,
                        applied: false
                    });
                }
                
                // Verificar variables no utilizadas
                // (Simplificado, en la realidad necesitaría un análisis AST)
                
                // Verificar indentación inconsistente
                const indentations = code.match(/^(\s+)\w+/gm) || [];
                const uniqueIndentations = new Set(indentations.map(i => i.match(/^(\s+)/)[1].length));
                if (uniqueIndentations.size > 1) {
                    result.fixes.push({
                        description: 'Indentación inconsistente detectada',
                        applied: false
                    });
                }
            }
            
            // Ejemplo para JavaScript
            if (language === 'javascript') {
                // Verificar uso de var en lugar de let/const
                if (/\bvar\b/.test(code)) {
                    const fixedCode = code.replace(/\bvar\b/g, 'let');
                    result.fixes.push({
                        description: 'Reemplazar "var" por "let" para mejor scope de variables',
                        applied: true
                    });
                    result.fixedCode = fixedCode;
                }
                
                // Verificar falta de punto y coma
                if (!/;\s*$/.test(code)) {
                    result.fixes.push({
                        description: 'Posible falta de punto y coma al final de declaraciones',
                        applied: false
                    });
                }
            }
        }
        
        return result;
    }
    
    /**
     * Intenta corregir automáticamente el código basado en el diagnóstico
     * @param {string} code - El código a corregir
     * @param {string} language - El lenguaje del código
     * @param {string} errorMessage - Mensaje de error opcional
     * @returns {Object} Código corregido y detalles
     */
    autoFix(code, language, errorMessage = '') {
        const diagnosis = this.diagnose(code, language, errorMessage);
        
        // Si no se encontraron problemas o no se pudieron aplicar correcciones
        if (!diagnosis.success || diagnosis.fixes.length === 0) {
            return {
                success: false,
                message: 'No se pudieron aplicar correcciones automáticas',
                original: code,
                fixed: code
            };
        }
        
        // Generar explicación de los cambios
        const appliedFixes = diagnosis.fixes.filter(fix => fix.applied);
        const explanation = appliedFixes.length > 0 
            ? `Se aplicaron ${appliedFixes.length} correcciones: ${appliedFixes.map(f => f.description).join(', ')}`
            : 'No se pudieron aplicar correcciones automáticas';
        
        return {
            success: appliedFixes.length > 0,
            message: explanation,
            fixes: diagnosis.fixes,
            original: code,
            fixed: diagnosis.fixedCode
        };
    }
}

// Exportar para uso en navegador o Node.js
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = DebugAI;
} else {
    window.DebugAI = DebugAI;
}
